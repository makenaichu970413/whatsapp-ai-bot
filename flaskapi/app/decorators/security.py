from functools import wraps
import logging
import hashlib
import hmac
import json
from app.config import APP_SECRET

import pydash as py_
from flask import jsonify, request


def validate_signature(payload, signature):
    """
    Validate the incoming payload's signature against our expected signature
    """
    # logging.info(f"1.2 - validate_signature - signature : \n{signature}")
    # logging.info(f"1.2 - validate_signature - APP_SECRET : \n{APP_SECRET}")
    
    # Use the App Secret to hash the payload
    payload = payload.encode("utf-8")
    expected_signature = hmac.new(
        bytes(APP_SECRET, "latin-1"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()
    
    bool = hmac.compare_digest(expected_signature, signature)
    # logging.info(f"1.2 - validate_signature - expected_signature : \n{expected_signature}")
    # logging.info(f"1.2 - validate_signature - bool: {bool}")

    # Check if the signature matches
    return bool 


def signature_required(f):
    """
    Decorator to ensure that the incoming requests to our webhook are valid and signed with the correct signature.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # logging.info(f"1.1 - signature_required - request.headers : \n{request.headers}") 
        # logging.info(f"1.1 - signature_required - request.data : \n{request.data}") 
        signature = request.headers.get("X-Hub-Signature-256", "")[7:] #! Removing 'sha256='
        if not validate_signature(request.data.decode("utf-8"), signature):
            logging.info("1.1 - signature_required - Signature verification failed!")
            return jsonify({"status": "error", "message": "Invalid signature"}), 403
        return f(*args, **kwargs)

    return decorated_function


