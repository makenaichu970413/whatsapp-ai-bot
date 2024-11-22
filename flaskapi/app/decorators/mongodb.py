import os
import logging
import json
import datetime
from functools import wraps
import pydash as py_
from pymongo import MongoClient
from flask import jsonify, request

from app.config import MONGO_URL, MONGODB_DATABASE, MONGODB_TABLE_CUSTOMER, MONGODB_TABLE_BILL


# Example
business = {
    "WHATSAPP_BUSINESS_ID": "",
    "OPENAI_API_KEY": "",
    "OPENAI_ASSISTANT_ID": ""
}

bill = {
    "WHATSAPP_BUSINESS_ID": "",
    "records": {}
}

# Connect to MongoDB
client = MongoClient(MONGO_URL)

# Select the database
db = client[MONGODB_DATABASE]

# Select the collection (table)
customers_collection = db[MONGODB_TABLE_CUSTOMER]
bills_collection = db[MONGODB_TABLE_BILL]

# current_month_year = datetime.now().strftime("%m/%Y")


def GetBusiness(data):
    temp = {"result":None, "error":None}
    WABusinessID = py_.get(data, 'entry[0].changes[0].value.metadata.phone_number_id', None)
    logging.info(f"3. mongodb_info - WABusinessID : {WABusinessID}") 
    
    if not WABusinessID:
        logging.info(f'3. mongodb_info - Invalid WABusinessID')
        temp["error"] = "Invalid WABusinessID"
        return temp
    
    # Retrieve the data
    business = customers_collection.find_one({"WHATSAPP_BUSINESS_ID": WABusinessID})
    logging.info(f"3. mongodb_info - business : {business}") 

    if not business:
        logging.info(f'3. mongodb_info - business "{WABusinessID}" is not found in MongoDB.')
        temp["error"] = "Invalid Customer"
        return temp
    
    temp["result"] = business
    return temp


# def CreateBusinessBill():
#     WABusinessID = ""
#     bill = {
#         "WHATSAPP_BUSINESS_ID": WABusinessID,
#         "records": {}
#     }
#     bills_collection.update_one(
#         {"WHATSAPP_BUSINESS_ID": WABusinessID},
#         {"$setOnInsert": bill},
#         upsert=True
#     )
#     print(f"Ensured document exists for WHATSAPP_BUSINESS_ID: {WABusinessID}")

# # 1. Insert a record dynamically for the current month and year if it doesn’t exist
# def InsertBillRecord():
#     default_month_record = {
#         "OPENAI_AMOUNT": 0,
#         "OPENAI_CALL_TIME": 0
#     }
#     WABusinessID = ""
#     bills_collection.update_one(
#         {"WHATSAPP_BUSINESS_ID": WABusinessID},
#         {
#             "$setOnInsert": {"WHATSAPP_BUSINESS_ID": WABusinessID},
#             "$set": {f"records.{WABusinessID}": default_month_record}
#         },
#         upsert=True
#     )
#     logging.info(f"Inserted record for {current_month_year} if it did not already exist.")

# # 2. Retrieve the record for the current month and year
# def GetBillRecord():
#     WABusinessID = ""
#     result = bills_collection.find_one(
#         {"WHATSAPP_BUSINESS_ID": WABusinessID},
#         {f"records.{current_month_year}" : 1}  # Project only the current month's data
#     )

#     # Extract and return the specific record for the current month
#     current_month_record = result.get("records", {}).get(current_month_year, "No record found for current month")
#     return current_month_record

# # 3. Update the record for the current month and year (if it already exists)
# def UpdateBillRecord(new_amount, new_call_time):
#     WABusinessID = ""
#     bills_collection.update_one(
#         {
#             "WHATSAPP_BUSINESS_ID": WABusinessID,
#             f"records.{current_month_year}": {"$exists": True}
#         },
#         {
#             "$set": {
#                 f"records.{current_month_year}.OPENAI_AMOUNT": new_amount,
#                 f"records.{current_month_year}.OPENAI_CALL_TIME": new_call_time
#             }
#         }
#     )
#     logging.info(f"Updated record for {current_month_year}.")


def mongodb_info(f):
    """
    Decorator to ensure that the incoming requests to our webhook are valid and signed with the correct signature.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        #? Get the business 
        data = json.loads(request.data.decode('utf-8'))
        temp = GetBusiness(data)
        
        if temp["error"]:
            return jsonify({"status": "error", "message": temp["error"]}), 403     
        business = temp["result"]
        
        return f(business, *args, **kwargs)

    return decorated_function

