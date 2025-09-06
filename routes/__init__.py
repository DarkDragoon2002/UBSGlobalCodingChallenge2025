from flask import Flask

app = Flask(__name__)
from routes import square
from routes import trivia
from routes import ticketing
from routes import princess_diaries
from routes import safeguard
from routes import spy_net
