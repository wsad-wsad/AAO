# from contextlib import asynccontextmanager
import requests

# from time import sleep
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from flask import Flask

from until.response import response
from SU import SUGW, search_web
from aiAgent import input_req


# # ini untuk start pas app awal dimulai dan dimatiin
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     yield

flapp = Flask(__name__)
fast_app = FastAPI()

fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("templates/index.html", "r") as f:
    home_html = f.read()


@flapp.route("/api/invest/<target>")
def mikir(target):
    try:
        agent = input_req(target)

        return response(200, agent, "success")

    except Exception as e:
        return response(500, str(e), "error")


@fast_app.get("/")
async def home():
    return HTMLResponse(home_html)

@fast_app.get("/api/SUGW/{target}")
def search_user(target: str):
    return SUGW(target)

@fast_app.get("/api/search-web/{target}")
def search_web_(target: str):
    return {"result": search_web(target, True)}

@fast_app.get("/api/main_go")
def main_go():
    return {"msg" : requests.get("http://localhost:8000/")}


@fast_app.get("/api/")
def health():
    return {"status": "ok"}


# flapp pakai middleware WSGI trs di mount ke fast_app
fast_app.mount("/", WSGIMiddleware(flapp))