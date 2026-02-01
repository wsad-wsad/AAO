from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from flask import Flask

# import until.type as type # Aku coment biar gak editor gak berisik warning-warning
from aiAgent import AiAgent
from until.response import response


# ini untuk start pas app awal dimulai dan dimatiin
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


flapp = Flask(__name__)
fast_app = FastAPI()


# area testing


@flapp.route("/api/test")
def index_test():
    return response(200, None, "Hello, World!")


@flapp.route("/api/search/<target>")
def mikir(target):
    try:
        agent = AiAgent(target)

        report = agent.run()
        return response(200, report, "success")

    except Exception as e:
        return response(500, str(e), "error")


@fast_app.get("/")
def index():
    return {"message": "Hello, World!"}


# flapp pakai middleware WSGI trs di mount ke fast_app
fast_app.mount("/", WSGIMiddleware(flapp))
