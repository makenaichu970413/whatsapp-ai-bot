import sys
import os
import logging
from urllib.parse import quote_plus

from dotenv import load_dotenv

#? Should set the path at the begining to import the ".env" file correctly 
dotenv_path = os.path.join(os.getcwd(), '.env')
load_dotenv(dotenv_path=dotenv_path)
print(f"DOTENV_PATH: {dotenv_path}")
for key, value in os.environ.items():
    print(f"{key}: {value}")

def get_env_var(key):
    value = os.getenv(key)
    return value.strip() if value else None

#? WhatsApp API 
ACCESS_TOKEN = get_env_var("ACCESS_TOKEN")
RECIPIENT_WAID = get_env_var("RECIPIENT_WAID")
PHONE_NUMBER_ID = get_env_var("PHONE_NUMBER_ID")
VERSION = get_env_var("VERSION")
APP_ID = get_env_var("APP_ID")
APP_SECRET = get_env_var("APP_SECRET")
VERIFY_TOKEN = get_env_var("VERIFY_TOKEN")

#? OPEN AI
OPENAI_API_KEY = get_env_var("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = get_env_var("OPENAI_ASSISTANT_ID")

#? MONGO DB
MONGODB_USER=get_env_var("MONGODB_USER")
MONGODB_PASSWORD=get_env_var("MONGODB_PASSWORD")
MONGODB_IP=get_env_var("MONGODB_IP")
MONGODB_PORT=get_env_var("MONGODB_PORT")
MONGODB_DATABASE=get_env_var("MONGODB_DATABASE")
MONGODB_TABLE_CUSTOMER=get_env_var("MONGODB_TABLE_CUSTOMER")
MONGODB_TABLE_BILL=get_env_var("MONGODB_TABLE_BILL")
MONGO_URL = f"mongodb://{quote_plus(MONGODB_USER)}:{quote_plus(MONGODB_PASSWORD)}@{MONGODB_IP}:{MONGODB_PORT}"


#? Log Files 
LOG_FILE = {
    "MESSAGES" : "messages.json",
    "REQUESTS" : "requests.json",
    "RPM" : "rpm.json"
}

#? Interval Check Event
REQUESTS_PER_MINUTES = 5
RPM_SECONDS = 120
DELETE_FILES_INTERVAL_SECONDS = 60


def load_configurations(app):
    app.config["ACCESS_TOKEN"] = ACCESS_TOKEN
    app.config["YOUR_PHONE_NUMBER"] = get_env_var("YOUR_PHONE_NUMBER")
    app.config["APP_ID"] = APP_ID
    app.config["APP_SECRET"] = APP_SECRET
    app.config["RECIPIENT_WAID"] = RECIPIENT_WAID
    app.config["VERSION"] = VERSION
    app.config["PHONE_NUMBER_ID"] = PHONE_NUMBER_ID
    app.config["VERIFY_TOKEN"] = VERIFY_TOKEN
    print(f'load_configurations: {app.config}')


def configure_logging(app):
    app.logger.disabled = True
    logging.getLogger('werkzeug').disabled = True
    logging.basicConfig(
        level=logging.INFO,
        # format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        format="%(message)s",
        stream=sys.stdout,
        force=True
    )
    logging.info("Logging configured successfully")