from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from flask import Flask

import until.type as type
from aiAgent import input
from until.response import response


# ini untuk start pas app awal dimulai dan dimatiin
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


flapp = Flask(__name__)
fast_app = FastAPI()


@flapp.route("/api/scan/<target>")
def mikir(target):
    try:
        agent = input(target)

        return response(200, agent, "success")

    except Exception as e:
        return response(500, str(e), "error")


@fast_app.get("/")
def index():
    return response()


# flapp pakai middleware WSGI trs di mount ke fast_app
fast_app.mount("/", WSGIMiddleware(flapp))
