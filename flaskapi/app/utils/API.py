import requests
from flask import jsonify
import pydash as py_
import json
import logging

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    # logging.info(f"Body: {response.text}")


def Post(props):
    try:
        url = py_.get(props, 'url', "")
        data = py_.get(props, 'data', {})
        headers = py_.get(props, 'headers', {})
        timeout = py_.get(props, 'timeout', 10)
        
        request_args = {
            "url": url,
            "data": json.dumps(data),
            "headers": headers,
            "timeout": timeout,
        }
         
        response = requests.post(**request_args)
        response.raise_for_status()
    except requests.Timeout:
        logging.error("Timeout occurred while sending POST request")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        logging.error(f"POST request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send POST request"}), 500
    else:
        log_http_response(response)
        return response


def Get(props):
    try:
        url = py_.get(props, 'url')
        params = py_.get(props, 'params', None)
        headers = py_.get(props, 'headers')
        timeout = py_.get(props, 'timeout', 10)
        
        request_args = {
            "url": url,
            "headers": headers,
            "timeout": timeout
        }
        if params: request_args["params"] = params

        response = requests.get(**request_args)
        response.raise_for_status()
    except requests.Timeout:
        logging.error("Timeout occurred while sending GET request")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        logging.error(f"GET request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send GET request"}), 500
    else:
        log_http_response(response)
        return response


def Delete(props):
    try:
        url = py_.get(props, 'url')
        headers = py_.get(props, 'headers')
        timeout = py_.get(props, 'timeout', 10)
        
        request_args = {
            "url": url,
            "headers": headers,
            "timeout": timeout
        }
        
        response = requests.delete(**request_args)
        response.raise_for_status()
    except requests.Timeout:
        logging.error("Timeout occurred while sending DELETE request")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        logging.error(f"DELETE request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send DELETE request"}), 500
    else:
        log_http_response(response)
        return response


def Patch(props):
    try:
        url = py_.get(props, 'url')
        data = py_.get(props, 'data')
        headers = py_.get(props, 'headers')
        timeout = py_.get(props, 'timeout', 10)
        
        request_args = {
            "url": url,
            "data": json.dumps(data),
            "headers": headers,
            "timeout": timeout
        }
        
        response = requests.patch(**request_args)
        response.raise_for_status()
    except requests.Timeout:
        logging.error("Timeout occurred while sending PUT request")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        logging.error(f"PUT request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send PUT request"}), 500
    else:
        log_http_response(response)
        return response
    
