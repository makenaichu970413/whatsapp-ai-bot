import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.openai import UploadFile, CreateAssistant, GenerateResponse

 
# --------------------------------------------------------------
# Create assistant at 1st time
# --------------------------------------------------------------
print(f"Creating Assistant ...")
file = UploadFile("../data/airbnb-faq.pdf")
print(f"Uploaded Assistant File: ", file)
assistant = CreateAssistant(file)
print(f"Created Assistant: ", assistant)


# --------------------------------------------------------------
# Test assistant
# --------------------------------------------------------------

# new_message = GenerateResponse("What's the check in time?", "123", "John")

# new_message = GenerateResponse("What's the pin for the lockbox?", "456", "Sarah")

# new_message = GenerateResponse("What was my previous question?", "123", "John")

# new_message = GenerateResponse("What was my previous question?", "456", "Sarah")
