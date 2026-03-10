from contextlib import asynccontextmanager
from typing import Annotated

from psycopg_pool import AsyncConnectionPool
from pymemcache.client.base import PooledClient

# from time import sleep
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from flask import Flask

from SU.SUGW import SUGW
from aiAgent import input_req
import db
from security.login import g_auth_router
from security.jwt_utils import JWT_payload, current_user

from setting import Settings
setting = Settings()

# DB pool start
with open("/run/secrets/postgres_password", "r") as f:
    POSTGRES_PASSWORD = f.read()
conn_str = f"host={setting.POSTGRES_HOST} port={setting.POSTGRES_PORT} dbname={setting.POSTGRES_DB} user={setting.POSTGRES_USER} password={POSTGRES_PASSWORD}"

# app start and end
@asynccontextmanager
async def lifespan(app: FastAPI):
    db.memcache_pool = PooledClient(
        f"{setting.MEMCACHED_HOST}:{setting.MEMCACHED_PORT}",
        max_pool_size=4
    )

    db.postgres_pool = AsyncConnectionPool(conninfo=conn_str)
    await db.postgres_pool.open()

    yield
    
    await db.postgres_pool.close()
    db.memcache_pool.close()

flapp = Flask(__name__)
fast_app = FastAPI(lifespan=lifespan)
fast_app.include_router(g_auth_router, prefix="/api/auth/google")

fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=[setting.DOMAIN_HOST],
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("templates/index.html", "r") as f:
    home_html = f.read()

@fast_app.get("/")
async def home(user: Annotated[JWT_payload, Depends(current_user)]):
    return HTMLResponse(home_html)

@fast_app.get("/api/invest/{target}")
def mikir(target: str, user: Annotated[JWT_payload, Depends(current_user)]):
    return input_req(target)

@fast_app.get("/api/SUGW/{username}")
async def SUGW_api(username: str, full_name: str, user_top_details: str):
    return await SUGW(username, full_name, user_top_details)

@fast_app.get("/api/")
async def health():
    return {"status": "ok"}

@fast_app.exception_handler(401)
async def http_exception_handler(request: Request, exc: HTTPException):
    return RedirectResponse("http://localhost:8080/api/auth/google/login", 302)

# flapp pakai middleware WSGI trs di mount ke fast_app
fast_app.mount("/", WSGIMiddleware(flapp))
