from flask import Flask

from until.aiAgent import AiAgent
from until.response import response

app = Flask(__name__)
# Untuk sekarang pakai flask dulu, kalau udah gede bisa dimigrasiin ke FastAPI


# area testing
@app.route("/api/test")
def index():
    return response(200, None, "Hello, World!")


@app.route("/api/mikir/<username>")
def mikir(username):
    try:
        ai_agent = AiAgent(username)
        return response(200, ai_agent.mikir_ai(), "success")
    except Exception as e:
        return response(500, str(e), "error")


if __name__ == "__main__":
    app.run(debug=True)
