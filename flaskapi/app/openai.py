from openai import OpenAI
import shelve
import os
import time
import logging
import threading
from dotenv import load_dotenv
import pydash as py_

# from app.config import OPENAI_API_KEY, OPENAI_ASSISTANT_ID


load_dotenv()

# --------------------------------------------------------------
# Upload file
# --------------------------------------------------------------
def UploadFile(path, OPENAI_API_KEY):
    # Upload a file with an "assistants" purpose
    client = OpenAI(api_key=OPENAI_API_KEY)
    file = client.files.create(
        file=open(path, "rb"), purpose="assistants"
    )
    
    return file


# --------------------------------------------------------------
# Create assistant
# --------------------------------------------------------------
def CreateAssistant(file, OPENAI_API_KEY):
    """
    You currently cannot set the temperature for Assistant via the API.
    """
    file_id = file.id
    print("Uploaded FileID: ", file_id)
    client = OpenAI(api_key=OPENAI_API_KEY)
    assistant = client.beta.assistants.create(
        name="WhatsApp AirBnb Assistant",
        instructions="You're a helpful WhatsApp assistant that can assist guests that are staying in our Paris AirBnb. Use your knowledge base to best respond to customer queries. If you don't know the answer, say simply that you cannot help with question and advice to contact the host directly. Be friendly and funny.",
        tools=[{"type": "file_search"}],
        model="gpt-4-1106-preview",
        # file_ids=[file_id],
        tool_resources={"file_search": {"vector_stores": [{"file_ids": [file_id]}]}}
    )
    logging.info(f"Created Assistant: {assistant}")
    return assistant


# --------------------------------------------------------------
# Thread management
# --------------------------------------------------------------
# Use context manager to ensure the shelf file is closed properly
def IsThreadExists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)


def StoreThread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id
    
    
# Function to check and reset threads older than 1 hour
# def reset_old_threads():
#     with shelve.open("threads_db", writeback=True) as threads_shelf:
#         for wa_id, data in list(threads_shelf.items()):
#             created_at = data.get("created_at")
#             if created_at and (datetime.datetime.now() - created_at).total_seconds() > 3600:
#                 logging.info(f"Resetting thread for wa_id {wa_id}")
#                 # Reset the thread by removing it from the shelf
#                 del threads_shelf[wa_id]
                
                
# --------------------------------------------------------------
# Run assistant
# --------------------------------------------------------------
def RunAssistant(client, thread, business):
    # Retrieve the Assistant
    OPENAI_ASSISTANT_ID=py_.get(business,"OPENAI_ASSISTANT_ID")
    assistant = client.beta.assistants.retrieve(OPENAI_ASSISTANT_ID)
    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        # instructions=f"You are having a Conversation with {name}",
    )

    #? Wait for completion with a timeout mechanism    
    # https://platform.openai.com/docs/assistants/how-it-works/runs-and-run-steps#:~:text=under%20failed_at.-,Polling%20for%20updates,-In%20order%20to
    start_time = time.time()
    timeout = 60 # Timeout after 60 seconds
    while run.status != "completed":
        if time.time() - start_time > timeout:  
            logging.warning(f'Run taking too long, terminating run "{run.id}"')
            # client.beta.threads.runs.terminate(thread_id=thread.id, run_id=run.id)
            run = None
            break
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    
    # If responsd take more than 60s then timeout and return None
    if not run: return None
    
    # Retrieve the Messages
    response = client.beta.threads.messages.list(thread_id=thread.id)
    logging.info(f"OpenAI_ASSISTANT_RESPONSE: \n{response}\n\n")
    
     # Extract token usage information
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = response.usage.total_tokens

    # Calculate cost (example cost per token, adjust as needed)
    cost_per_token = 0.0001  # Example cost per token
    total_cost = total_tokens * cost_per_token

    # Print the extracted information
    logging.info(f"Prompt Tokens: {prompt_tokens}")
    logging.info(f"Completion Tokens: {completion_tokens}")
    logging.info(f"Total Tokens: {total_tokens}")
    logging.info(f"Cost for this response: ${total_cost:.6f}")
    
    message = response.data[0].content[0].text.value
    logging.info(f"Generated message: {message}")
    return message


# --------------------------------------------------------------
# Generate response
# --------------------------------------------------------------
def GenerateResponse(props, business):
    logging.info(f'OPENAI GenerateResponse - business: {business}')
    
    OPENAI_API_KEY=py_.get(business,"OPENAI_API_KEY")
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    body = py_.get(props, 'body', None)
    contact =  py_.get(body, 'entry[0].changes[0].value.contacts[0]', None)
    waID = py_.get(contact, "wa_id", None)
    name = py_.get(contact, "profile.name", None) 
    content = py_.get(props, 'content', None)
    

    # Check if there is already a thread_id for the wa_id
    threadID = IsThreadExists(waID)

    temp = {"body":body, "content": content, "threadID": threadID}
    logging.info(f"Generating response with temperature setting: \n{temp}")
    logging.info("ChatGPT is generating a response...")

    # If a thread doesn't exist, create one and store it
    if threadID is None:
        logging.info(f"Creating new thread for {name} with wa_id {waID}")
        thread = client.beta.threads.create()
        StoreThread(waID, thread.id)
        threadID = thread.id

    # Otherwise, retrieve the existing thread
    else:
        logging.info(f"Retrieving existing thread for {name} with wa_id {waID}")
        thread = client.beta.threads.retrieve(threadID)
        
    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=threadID,
        role="user",
        content=content,
    )

    # Run the assistant and get the new message
    response = RunAssistant(client, thread, business)
    logging.info(f'Sending message to "{name}": {response}')
    return response
