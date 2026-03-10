from datetime import datetime, timedelta, UTC
from pydantic import BaseModel, EmailStr, field_validator, ValidationError

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import InvalidTokenError
from secrets import token_urlsafe

from main_py.setting import Settings
setting = Settings()

class JWT_payload(BaseModel):
    sub: str
    email: EmailStr
    exp: datetime
    iat: datetime   # init time
    type: str
    
    @field_validator("exp", mode="after")
    @classmethod
    def validate_exp(cls, value):
        if value <= datetime.now(UTC):
            raise ValueError("Token expired")
        return value
    
def credentials_exception(message: str = "Could not validate credentials"):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )   

def create_access_token(user_id: int, email: str) -> str:
    payload = JWT_payload(
        sub=str(user_id),
        email=email,
        exp=datetime.now(UTC) + timedelta(minutes=setting.JWT_ACSESS_TOKEN_EXPIRE_MINUTES),
        iat=datetime.now(UTC),
        type="access",
    ).model_dump()
    return jwt.encode(payload, setting.JWT_SECRET_KEY, algorithm=setting.JWT_ALGORITHM)

def create_refresh_token():
    return token_urlsafe(64)

def decode_access_token(token: str) -> JWT_payload:
    try:
        payload = jwt.decode(token, setting.JWT_SECRET_KEY, algorithms=[setting.JWT_ALGORITHM])
        payload = JWT_payload(**payload)
        
        if payload.type != "access":
            raise credentials_exception("Invalid token type")
        elif payload.sub is None:
            raise credentials_exception()

        return payload
    
    except InvalidTokenError:
        raise credentials_exception()

    except ValidationError:
        raise credentials_exception()
    
def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False))
):
    # Support both Bearer header (API clients) and cookie (browser)
    token = None
    if credentials:
        token = credentials.credentials          # Authorization: Bearer <token>
    elif cookie_token := request.cookies.get("access_token"):
        token = cookie_token                     # browser cookie

    if not token:
        raise credentials_exception()

    payload = decode_access_token(token)         # raises 401 if invalid/expired

    return {"id": payload.sub, "email": payload.email}