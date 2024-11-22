import logging
import json
import os
import re
import threading
from datetime import datetime, timedelta
import pydash as py_

from app.config import LOG_FILE

log_folder = "log"

def WriteExpiredLog(props):
    
    id = py_.get(props, "id", "") #!
    filename = py_.get(props, "filename", "") #!
    expired_minutes = py_.get(props, "expired_minutes", 5) #?
    pValue = py_.get(props, "value", None) #?
    
    data = GetLog(filename)
    
    # Get current time
    current_time = datetime.now()

    # Calculate expiration time
    expired_time = current_time + timedelta(minutes=expired_minutes)
    
    # Remove entries that are already expired
    logging.info(f"PREV_LOG_LEN: {len(data.items())}")
    new_data = {}
    for key, value in data.items():
        recorded_expired_time = datetime.fromisoformat(value["expired_time"])
        is_valid =  recorded_expired_time > current_time
        logging.info(f"PREV_KEY {key}: {value}; is_valid: {is_valid}")
        if is_valid:
            logging.info(f"PREV_VALID_KEY {key}: {value}") 
            new_data[key] = value
    
    # Add or update the request in the log with the expiration time
    obj = {"expired_time": expired_time.isoformat()}
    if pValue: obj["value"] = pValue
    new_data[id] = obj

    # Write updated log data back to the file   
    # logging.info(f"WRITE_LOG: {{'{id}': {obj}}}")
    UpdateLog(filename, new_data) 
    

def GetLog(filename):
    # Load existing log data
    data = {} 
    file_path = os.path.join(log_folder, filename)
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}
    # logging.info(f'GET_LOG "{filename}": {data}')            
    return data


def UpdateLog(filename, data):
    # Load existing log data
    file_path = os.path.join(log_folder, filename)
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    # logging.info(f'UPDATE_LOG "{filename}": {data}')            


def CleanText(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


def SetInterval(func, seconds):
    def wrapper():
        SetInterval(func, seconds)  # Schedule the next call
        func()  # Call the function
    timer = threading.Timer(seconds, wrapper)  # Create a timer thread
    timer.start()
    return timer  # Return the timer object in case you need to cancel it later


def DeleteOldFiles(directory, age_minutes=5):
    # Define the age threshold for deletion
    age_threshold = datetime.now() - timedelta(minutes=age_minutes)

    # List all files in the directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        # Check if it is a file (not a directory)
        if os.path.isfile(file_path):
            # Get the file's creation time
            file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))

            # Check if the file is older than the threshold
            if file_creation_time < age_threshold:
                try:
                    os.remove(file_path)
                    logging.info(f"Deleted: {file_path}")
                except Exception as e:
                    logging.info(f"Error deleting {file_path}: {e}")