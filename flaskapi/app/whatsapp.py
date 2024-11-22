import logging
import os
import mimetypes
import json
import threading
from flask import jsonify
import requests
from pydash import py_
import whisper

from app.config import VERSION, PHONE_NUMBER_ID, ACCESS_TOKEN, LOG_FILE, REQUESTS_PER_MINUTES
from app.openai import GenerateResponse
from app.utils.function import GetLog, UpdateLog, WriteExpiredLog, CleanText
from app.utils.API import Post, Get

# Log Files
log_requests_filename = LOG_FILE["REQUESTS"]
log_messages_filename = LOG_FILE["MESSAGES"]
log_rpm_filename = LOG_FILE["RPM"]


timers = {} # {waID: threading.Timer}
messages = GetLog(log_messages_filename) # {waID: {"content": content, "body": body}[]}
rpm = GetLog(log_rpm_filename) # {"count":0, "pending_contents": {"waID": []{"content": content, "body": body} } 


def Conversation(waID, contents, business): 
    ai_call_time = 1 # The time of calling OpenAI API in different company business flow 
    count = rpm["count"]
    bool = count + ai_call_time <= REQUESTS_PER_MINUTES
    temp = {"waID": waID, "count": count, "bool": bool}
    logging.info(f'\n\nConversation: {temp}' )
    if bool:
        #? contents: []{"content": string, "body": whatsapp_body}
        body = py_.get(contents,"[0].body", None)
        combined_content = "\n".join(item['content'] for item in contents)
        logging.info(f"combined_content: {combined_content}")    
        
        #? OpenAI Integration
        response = GenerateResponse({"content": combined_content, "body": body}, business)
        # response = combined_content #! TEST
        AddRPMCount()
        RemoveRPMPendingContents(waID)
        
        if response: 
            response = CleanText(response)

            #? Reply message to customer in WhatsApp 
            ReplyMessage({"response":response, "body": body})
        
            # Remove the timer from the dictionary after execution
            if waID in timers:
                del timers[waID]
                logging.info(f"Timer {waID} removed from dictionary.")

            if waID in messages:
                del messages[waID]
                UpdateLog(log_messages_filename, messages)
                logging.info(f"Messages {waID} removed from dictionary.")
    else:
        AddRPMPendingContents(waID, contents)       


def Listen(body, business, delay_seconds=5):
    message = py_.get(body, 'entry[0].changes[0].value.messages[0]', None)
    content = py_.get(message, 'text.body', None)
    contact = py_.get(body, 'entry[0].changes[0].value.contacts[0]', None)
    waID = py_.get(contact, "wa_id", None)
    
    if not content : return

    # Check if a timer with the same ID exists
    if waID in timers:
        # Cancel the existing timer
        timers[waID].cancel()
        logging.info(f"Existing timer {waID} cancelled.")

    # Add a incoming new content from WhatsApp and update contents list argument and reset timer
    contents = []
    if waID in messages:
        contents = messages[waID]
    contents.append({"content": content, "body": body})
    messages[waID] = contents
    UpdateLog(log_messages_filename, messages)
    
    # Create a new Timer object
    new_timer = threading.Timer(delay_seconds, Conversation, args=(waID, contents, business))

    # Store the new Timer object in the dictionary
    timers[waID] = new_timer

    # Start the new timer
    new_timer.start()
    logging.info(f"New timer {waID} started with a delay of {delay_seconds} seconds.")


def ReplyMessage(props):
    body = py_.get(props, 'body', None)
    contact =  py_.get(body, 'entry[0].changes[0].value.contacts[0]', None)
    waID = py_.get(contact, "wa_id", None)
    name = py_.get(contact, "profile.name", None)
    message = py_.get(body, 'entry[0].changes[0].value.messages[0]', None)
    messageID = py_.get(message, 'id', None) # Reply the message by Tag the customer message
    
    response = py_.get(props, 'response', None)
    
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": waID,
        "type": "text",
        "text": {"preview_url": False, "body": response},
    }
    if messageID: data["context"] = {"message_id": messageID}
    
    # Message Topic Endpoint 
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    
    logging.info(f"ReplyMessage: {props}")
    logging.info(f"messageID: {messageID}")
    logging.info(f"WhatsApp sending data: {data}")
    logging.info("WhatsApp is sending a message...")
    Post({"url":url, "headers":headers, "data":data})
     

def ProcessTextMessage(body, business):
    message = py_.get(body, 'entry[0].changes[0].value.messages[0]', None)
    messageID = py_.get(message, 'id', None)
    # Log the Message ID after sent the replied responses
    logging.info(f"message_id: {messageID}")
    if messageID: WriteExpiredLog({"id": messageID, "filename": log_requests_filename})

    Listen(body, business)


def ProcessAudioMessage(body, business): 
    
    message = py_.get(body, 'entry[0].changes[0].value.messages[0]', None)
    messageID = py_.get(message, 'id', None)
    audio = py_.get(message, 'audio', None)
    audioID = py_.get(audio, 'id', None)

    #? Get the WhatsApp Media data by <media_id>
    media_url = f"https://graph.facebook.com/{VERSION}/{audioID}/"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    # logging.info(f"py_audio: {audio}")
    # logging.info(f"py_audio_url: {media_url}")
    mediaRES = Get({"url":media_url, "headers": headers})
    # logging.info(f"py_audio_response: {response}")
    media = mediaRES.json()
    download_url = py_.get(media, "url", None)
    filename = py_.get(media, "id", None)
    file_size = py_.get(media, "file_size", None)
    mime_type = py_.get(media, "mime_type", None)
    extension = mimetypes.guess_extension(mime_type) if mime_type else None
    filename = f'{filename}{extension if extension else ""}'
    
    try:
        # Log the Message ID after sent the replied responses
        logging.info(f"message_id: {messageID}")   
        if messageID: WriteExpiredLog({"id": messageID, "filename": log_requests_filename})
        
        downloadRES = Get({"url":download_url, "headers": headers})        
        # response = requests.get(download_url, headers=headers, timeout=10)  # 10 seconds timeout as an example
        # response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        
        # Ensure the 'media' directory exists
        os.makedirs('media', exist_ok=True)

        # Full path to save the file
        file_path = os.path.join('media', filename)
        
        # Download the file into "/media"
        with open(file_path, 'wb') as file:
            for chunk in downloadRES.iter_content(chunk_size=file_size): 
                file.write(chunk)

        # logging.info(f"file_path: {file_path}")

        try:
            logging.info(f"TRANSCRIBE Starting...")
            
            # Load the Whisper model
            model = whisper.load_model("base")
            # logging.info(f"TRANSCRIBE_MODEL: {model}")
            
            # Transcribe the audio file into text
            transcribe = model.transcribe(file_path)
            content = transcribe['text']
            
            logging.info(f"TRANSCRIBE: {content}")
            os.remove(file_path)
            # logging.info(f"Deleted file: {file_path}")
        except OSError as e:
            logging.error(f"Error deleting file {file_path}: {e}")
        else:
            logging.error("Transcription failed or returned empty text.")
        
        # OpenAI Integration
        #? Update the Transcribe text to follow the WhatsApp "...text.body" 
        py_.set_(body, 'entry[0].changes[0].value.messages[0].text.body', content)
        Listen(body, business)
            
    # This will catch any general request exception
    except (requests.RequestException) as e:  
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
           

def MessageType(body):    
    """
    Check if the incoming webhook event has a valid WhatsApp TEXT message structure.
    """
    data = py_.get(body, 'entry[0].changes[0].value.messages[0]', None)
    type = py_.get(data, "type", None)
    # logging.info(f"py_type: {type}")
    return type


def MessageOrigin(body):
    """
    Detects whether the message is sent by the business or customer based on the webhook payload.
       
    Returns: 'Status Update' if it's a message status update.
    """
    # Check if the payload contains 'statuses' field -> Status update for business-sent messages
    statuses = py_.get(body, 'entry[0].changes[0].value.statuses[0]', None)
    status = py_.get(statuses, 'status', None) #? "sent" | "delivered" | "read"
    if status:
        return "Business" 
    else:
        return "Customer"
  

def ResetRPM(): 
    logging.info(f"\n\n================ResetRPM================\n\n")          
    rpm["count"] = 0
    UpdateLog(log_rpm_filename, rpm)
    
    #? By calling .copy(), to avoiding changes during the iteration.
    pending_contents = rpm["pending_contents"]
    copied = pending_contents.copy().items()
    lock = threading.Lock()
    with lock:
        for waID, contents in copied:
            # Safely access dictionary within this block
            Conversation(waID, contents)
            pass
    

def AddRPMCount():
    rpm["count"] = rpm["count"] + 1
    UpdateLog(log_rpm_filename, rpm)
    

def AddRPMPendingContents(waID, contents):
    pending_contents = rpm["pending_contents"]
    pending_contents[waID] = contents
    rpm["pending_contents"] = pending_contents
    UpdateLog(log_rpm_filename, rpm)
    
    
def RemoveRPMPendingContents(waID):
    pending_contents = rpm["pending_contents"]
    logging.info(f'BEFORE rpm["pending_contents"]: {len(rpm["pending_contents"].items())}')          
    
    if waID in pending_contents:
        del pending_contents[waID]     
        
    rpm["pending_contents"] = pending_contents
    logging.info(f'AFTER rpm["pending_contents"]: {len(rpm["pending_contents"].items())}')          
    UpdateLog(log_rpm_filename, rpm)    
