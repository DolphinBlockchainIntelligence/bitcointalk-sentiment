from flask import Flask
app = Flask(__name__)

@app.route("/init")
def hello():
    return "Hello World!"