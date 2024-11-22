import logging
import os
from pydash import py_ 

from app import create_app
from app.utils.function import GetLog, SetInterval, DeleteOldFiles
from app.config import LOG_FILE, RPM_SECONDS, DELETE_FILES_INTERVAL_SECONDS
from app.whatsapp import Conversation, ResetRPM
from app.decorators.mongodb import GetBusiness


# Define the interval function
def DeleteMediaFiles():
    path = os.path.join(os.getcwd(), 'media')
    DeleteOldFiles(path, 10) 

# Log Files
log_messages_filename = LOG_FILE["MESSAGES"]

app = create_app()    

if __name__ == "__main__":
    
    #? Send message from log after restart
    #? messages: {waID: []{"content": string, "body": whatsapp_body}}
    messages = GetLog(log_messages_filename) 
    for waID, contents in messages.items():
        data = py_.get(contents,"[0].body", None)
        business=GetBusiness(data)
        Conversation(waID, contents, business)
        
    #? Start the interval for RRM
    interval = SetInterval(ResetRPM, RPM_SECONDS)
    # Optional: Stop the interval after 60 seconds
    # threading.Timer(60, interval.cancel).start()    
    
    #? Every second check and delete the expired file
    SetInterval(DeleteMediaFiles, DELETE_FILES_INTERVAL_SECONDS)
    
    #? Start the Flask API Service 
    logging.info("Flask app started")
    app.run(host="0.0.0.0", port=5000)

    
