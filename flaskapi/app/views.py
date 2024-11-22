import logging
import json
from flask import Blueprint, request, jsonify, current_app
from pydash import py_

from app.decorators.security import signature_required
from app.decorators.message import validate_new_request
from app.decorators.mongodb import mongodb_info
from app.whatsapp import ProcessTextMessage, ProcessAudioMessage, MessageType

webhook_blueprint = Blueprint("webhook", __name__)


def handle_message(business):
    """
    Handle incoming webhook events from the WhatsApp API.

    This function processes incoming WhatsApp messages and other events,
    such as delivery statuses. If the event is a valid message, it gets
    processed. If the incoming payload is not a recognized WhatsApp event,
    an error is returned.

    Every message send will trigger 4 HTTP requests to your webhook: message, sent, delivered, read.

    Returns:
        response: A tuple containing a JSON response and an HTTP status code.
    """
    logging.info(f"5.1. handle_message - business : {business}") 
    
    data = request.get_json()
    logging.info(f"5.2. handle_message - data : {data}") 
    
    #? Check if it's a WhatsApp status update
    status = py_.get(data, 'entry[0].changes[0].value.statuses', None)
    logging.info(f"5.2. handle_message - status : {data}") 
    if (status):
        logging.info("5. - handle_message - Received a WhatsApp status update.")
        return jsonify({"status": "ok"}), 200

    try:
        # logging.info(f"WhatsApp Body: {body}")
        msg_type = MessageType(data)
        if msg_type == "text":
            ProcessTextMessage(data, business)
            return jsonify({"status": "ok"}), 200
        elif msg_type == "audio":
            ProcessAudioMessage(data, business)
            return jsonify({"status": "ok"}), 200
        else:
            # if the request is not a WhatsApp API event, return an error
            return (
                jsonify({"status": "error", "message": "Not a WhatsApp API event"}),
                404,
            )
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON")
        return jsonify({"status": "error", "message": "Invalid JSON provided"}), 400


# Required webhook verifictaion for WhatsApp
def verify():
    # Parse params from the webhook verification request
    mode = request.args.get("hub.mode") #? This value will always be set to subscribe.
    token = request.args.get("hub.verify_token") #? An int must pass back to meta after verified success.
    challenge = request.args.get("hub.challenge") #? A string that meta grab from the Verify Token field in App Dashboard.
    
    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == current_app.config["VERIFY_TOKEN"]:
            # Respond with 200 OK and challenge token from the request
            logging.info("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            logging.info("VERIFICATION_FAILED")
            return jsonify({"status": "error", "message": "Verification failed"}), 403
    else:
        # Responds with '400 Bad Request' if verify tokens do not match
        logging.info("MISSING_PARAMETER")
        return jsonify({"status": "error", "message": "Missing parameters"}), 400


@webhook_blueprint.route("/webhook", methods=["GET"])
def webhook_get():
    return verify()

@webhook_blueprint.route("/webhook", methods=["POST"])
@signature_required
@validate_new_request
@mongodb_info
def webhook_post(business):
    logging.info(f"4. webhook_post - business : {business}") 
    return handle_message(business)


