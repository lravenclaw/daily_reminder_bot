import os

# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 
# loading variables from .env file
load_dotenv() 

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

PORT = os.getenv("PORT")
URL = os.getenv("URL")