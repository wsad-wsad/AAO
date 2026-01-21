from flask import Flask

from lib.until.response import response

app = Flask(__name__)


@app.route("/")
def main():
    return response(200, None, "Hello World")


if __name__ == "__main__":
    app.run(debug=True)
