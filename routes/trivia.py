from flask import Flask, jsonify
import logging

from routes import app

logger = logging.getLogger(__name__)

@app.route('/trivia', methods=['GET'])
def trivia_get():
    result = {"answers": [4, 1, 2, 2, 3, 4, 4, 5, 4]}
    logging.info("My result :{}".format(result))
    return jsonify(result)
