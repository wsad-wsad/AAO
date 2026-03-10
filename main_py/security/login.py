from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.exceptions import HTTPException

import sys
import secrets
from urllib.parse import urlencode
import httpx

sys.path.insert(0, "/app")
from setting import Settings
import db
from security.jwt_utils import create_access_token, create_refresh_token

setting = Settings()
g_auth_router = APIRouter()

@g_auth_router.get("/login")
async def login():
    state = secrets.token_urlsafe(32)
    db.memcache_pool.set(f"g_oauth_state:{state}", True, 300) # 5 minutes ttl

    params = {
    "client_id": setting.GOOGLE_CLIENT_ID,
    "redirect_uri": setting.GOOGLE_REDIRECT_URI,
    "response_type": "code",
    "scope": "openid email profile",
    "state": state,
    "prompt": "select_account",
    }

    url = f"{setting.GOOGLE_AUTH_URL}?{urlencode(params)}"
    print(url)
    return RedirectResponse(url)

@g_auth_router.get("/callback")
async def callback(code: str, state: str):
    if not db.memcache_pool.get(f"g_oauth_state:{state}"):
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(setting.GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": setting.GOOGLE_CLIENT_ID,
            "client_secret": setting.GOOGLE_CLIENT_SECRET,
            "redirect_uri": setting.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        tokens = token_resp.json()

        # Fetch user info
        userinfo_resp = await client.get(
            setting.GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        userinfo = userinfo_resp.json()

    # Upsert user in Postgres
    async with db.postgres_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO UserCredentials (google_id, email, username)
                VALUES (%s, %s, %s)
                ON CONFLICT (google_id) DO UPDATE
                SET email = EXCLUDED.email, username = EXCLUDED.username
                RETURNING id
            """, (userinfo["sub"], userinfo["email"], userinfo["name"]))
            user_id = await cur.fetchone()
            user_id = user_id[0]
    
    access_token = create_access_token(user_id, userinfo["email"])
    
    refresh_token = create_refresh_token()
    db.memcache_pool.set(f"g_refresh_token:{user_id}", refresh_token, setting.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 3600 * 24)

    response = RedirectResponse("/")
    # JWT in httponly cookie (or return in JSON body for SPA/mobile)
    response.set_cookie("access_token", access_token, httponly=True, samesite="lax", max_age=setting.JWT_ACSESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="lax", max_age=setting.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 3600 * 24)
    return response

@g_auth_router.post("/refresh")
async def refresh(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise RedirectResponse(setting.GOOGLE_REDIRECT_URI)

    user_id = db.memcache_pool.get(f"g_refresh_token:{refresh_token}")
    if not user_id:
        raise RedirectResponse(setting.GOOGLE_REDIRECT_URI)

    # Rotate refresh token (invalidate old, issue new)
    db.memcache_pool.delete(f"g_refresh_token:{refresh_token}")
    new_refresh_token = create_refresh_token()
    db.memcache_pool.set(f"g_refresh_token:{user_id}", new_refresh_token, setting.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 3600 * 24)

    # Fetch email for new access token
    async with db.postgres_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT email FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="User not found")

    new_access_token = create_access_token(user_id, row[0])

    response = JSONResponse({"access_token": new_access_token})
    response.set_cookie("access_token", new_access_token, httponly=True, samesite="lax", max_age=setting.JWT_ACSESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie("refresh_token", new_refresh_token, httponly=True, samesite="lax", max_age=setting.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    return response


@g_auth_router.post("/logout")
async def logout(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        db.memcache_pool.delete(f"g_refresh_token:{refresh_token}")     # invalidate in Memcache immediately

    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response