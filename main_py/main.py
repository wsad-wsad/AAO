from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool

# from time import sleep
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import HTMLResponse, Response
from flask import Flask

from SU import SUGW
from until.response import ResponseApi
from aiAgent import input_req


with open("/run/secrets/postgres_password", "r") as f:
    postgres_password = f.read()
conn_str = f"host=postgres port=5432 dbname=AAO_DB user=my_user password={postgres_password}"
pool = AsyncConnectionPool(conninfo=conn_str)

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    yield
    pool.close()

flapp = Flask(__name__)
fast_app = FastAPI(lifespan=lifespan)

fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("templates/index.html", "r") as f:
    home_html = f.read()

response = ResponseApi()

@fast_app.get("/api/invest/{target}")
def mikir(target):
    try:
        agent = input_req(target)
        return response(agent)
    except Exception as e:
        return response(str(e), "error on internal server")

@fast_app.get("/")
async def home():
    return HTMLResponse(home_html)

@fast_app.get("/api/")
async def health():
    return {"status": "ok"}


# flapp pakai middleware WSGI trs di mount ke fast_app
fast_app.mount("/", WSGIMiddleware(flapp))
