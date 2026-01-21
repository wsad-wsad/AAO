from flask import Flask
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware 

from until.response import response

flask_app = Flask(__name__)
app = FastAPI()

@flask_app.route("/hi")
def main():
    return response(200, None, "Hello World")

@app.get("/health")
def health():
    return {"status": True}

app.mount("/" ,WSGIMiddleware(flask_app))
