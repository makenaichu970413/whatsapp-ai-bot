from functools import wraps
import logging
import json
from datetime import datetime, timedelta
import pydash as py_
from flask import current_app, jsonify, request

from app.config import LOG_FILE
from app.utils.function import GetLog



def IsNewRequest(id):
    filename = LOG_FILE["REQUESTS"]
    data = GetLog(filename)
    
    # Get current time
    current_time = datetime.now()

    # Check if the id exists and is not expired
    bool = True
    if id in data:
        expired_time = data[id]["expired_time"]
        if datetime.fromisoformat(expired_time) > current_time:
            bool = False
        else:
            bool = True

    logging.info(f"IS_NEW_REQUEST: {{'{id}': {bool}}}")
    return bool


def validate_new_request(f):
    """
    Decorator to check if the request ID already exists in your log file. 
    If it does, the decorator returns an error response.
    """
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        # Decode the byte string to a regular string
        # Parse the JSON string into a Python dictionary
        data = json.loads(request.data.decode('utf-8'))
        messageID = py_.get(data, 'entry[0].changes[0].value.messages[0].id', None)
        # Proceed with the original function if the ID is new
        if messageID and IsNewRequest(messageID):
            return f(*args, **kwargs)
        
        message = f"messageID {messageID} already exists"
        # logging.info(f"messageCCC: {data}")
        return jsonify({"status": "ok", "message": message}), 200
        
    return decorated_function
