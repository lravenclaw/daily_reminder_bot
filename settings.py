import os

# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 
# loading variables from .env file
load_dotenv() 

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
DB_FILE_NAME = os.getenv("DB_FILE_NAME")
ADMIN_ID = os.getenv("ADMIN_ID")