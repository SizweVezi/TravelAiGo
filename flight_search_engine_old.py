import os
from dotenv import load_dotenv, find_dotenv
from amadeus import client,  ResponseError
import json

#read local .env file
_ = load_dotenv(find_dotenv())

amadeus = client(
    api_key = os.environ.get(api_key),

)