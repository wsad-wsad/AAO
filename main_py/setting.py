from pydantic_settings import BaseSettings
from dotenv import load_dotenv


load_dotenv()
class Settings(BaseSettings):
    # app
    DOMAIN_HOST: str = "http://localhost:8080"  # host domain
    
    # google Oauth service
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    GOOGLE_REDIRECT_URI: str = "http://localhost:8080/api/auth/google/callback"
    GOOGLE_AUTH_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL: str = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL: str = "https://www.googleapis.com/oauth2/v3/userinfo"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACSESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # postgres
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str

    # memcached
    MEMCACHED_HOST: str = "memcached"
    MEMCACHED_PORT: int = 11211

    # AI api key
    GEMINI_API_KEY: str
    GROQ_API_KEY: str