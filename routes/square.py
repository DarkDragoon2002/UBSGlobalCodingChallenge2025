import json
import logging

from flask import request, jsonify

from routes import app

logger = logging.getLogger(__name__)

@app.route('/square', methods=['GET', 'POST'])
def evaluate():
    if request.method == 'GET':
        return jsonify({"usage": "POST JSON like { \"input\": 5 } to this endpoint."})
    data = request.get_json()
    return jsonify(data["input"] * data["input"])
