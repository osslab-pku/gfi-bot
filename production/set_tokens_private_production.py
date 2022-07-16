import pymongo
import os
from typing import Final
import json
import logging
import argparse

MONGO_URI: Final = "mongodb://mongodb:27020/"
SECRET_FILE_NAME: Final = "production/production_secrets.json"

db_client = pymongo.MongoClient(MONGO_URI)
gfi_db = db_client["gfibot"]

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--secret_file_name", default=SECRET_FILE_NAME)
    file_name = parser.parse_args().secret_file_name

    tokens_collection = gfi_db.get_collection("github_tokens")
    email_collection = gfi_db.get_collection("gmail_email")

    if not os.path.exists(file_name):
        logging.error(f"No secret file found: {file_name}")
        if tokens_collection.count_documents({}) == 0:
            logging.error("No tokens found in database, exiting")
            exit(1)
        else:
            logging.info(
                "No secret file found, but tokens found in database, continuing"
            )
            exit(0)

    tokens_collection.drop()
    email_collection.drop()

    with open(file_name, "r") as f:
        secrets = json.load(f)
        web_client_secrets = secrets["web_client"]
        git_app_secrets = secrets["git_app"]
        mail_secrets = secrets["mail"]
        if web_client_secrets == None and git_app_secrets == None:
            logging.info("no secrets found")
            exit(1)
        if web_client_secrets:
            web_client_id = web_client_secrets["id"]
            web_client_secret = web_client_secrets["secret"]
            if web_client_id != None and web_client_secret != None:
                tokens_collection.insert_one(
                    {
                        "app_name": "gfibot-webapp",
                        "client_id": web_client_id,
                        "client_secret": web_client_secret,
                    }
                )
            else:
                logging.error("no web client secrets found")
                exit(1)
        if git_app_secrets:
            git_app_id = git_app_secrets["id"]
            git_app_secret = git_app_secrets["secret"]
            if git_app_id != None and git_app_secret != None:
                tokens_collection.insert_one(
                    {
                        "app_name": "gfibot-githubapp",
                        "client_id": git_app_id,
                        "client_secret": git_app_secret,
                    }
                )
            else:
                logging.error("no git app secrets found")
                exit(1)
        if mail_secrets:
            email = mail_secrets["email"]
            password = mail_secrets["password"]
            if email != None and password != None:
                email_collection.insert_one(
                    {
                        "email": email,
                        "password": password,
                    }
                )
