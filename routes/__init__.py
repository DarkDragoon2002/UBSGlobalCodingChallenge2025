from flask import Flask

app = Flask(__name__)
from routes import square
from routes import trivia
