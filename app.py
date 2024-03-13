from flask import Flask
import pickle
import numpy as np
import json

app = Flask(__name__)

@app.route("/")
def say_hello():
    return "Hello, World!"


if __name__ == "__main__":
    app.run(debug=False,host='0.0.0.0')

