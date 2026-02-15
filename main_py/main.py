from contextlib import asynccontextmanager

# from time import sleep
from aiAgent import input_req
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from flask import Flask, render_template
from flask_cors import CORS
from SU import search_web
from until.response import response


# ini untuk start pas app awal dimulai dan dimatiin
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


flapp = Flask(__name__)
fast_app = FastAPI()
CORS(flapp)


@flapp.route("/api/invest/<target>")
def mikir(target):
    try:
        agent = input_req(target)

        return response(200, agent, "success")

    except Exception as e:
        return response(500, str(e), "error")


@fast_app.get("/")
def index():
    return render_template("index.html")


@fast_app.get("/api/search-user/{target}")
def search(target: str):
    return search_web(target, True)


@fast_app.get("/api/")
def health():
    return {"status": "ok"}


# flapp pakai middleware WSGI trs di mount ke fast_app
fast_app.mount("/", WSGIMiddleware(flapp))
