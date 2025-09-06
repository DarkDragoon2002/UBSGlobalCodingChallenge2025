from flask import Flask, jsonify
import logging

from . import app

app = Flask(__name__)

@app.route('/trivia', methods=['GET'])
def evaluate():
    result = {"answers": [4, 1, 2, 2, 3, 4, 4, 5, 4]}
    logging.info("My result :{}".format(result))
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
