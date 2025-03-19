import json
import os
import boto3
from botocore.exceptions import ClientError
from amadeus import Client, ResponseError
from datetime import datetime, date, timedelta
#from dotenv import load_dotenv, find_dotenv


# Function to retrieve Amadeus API keys from AWS Secrets Manager
def get_amadeus_api_keys():
        secret_name = "amadeus_secret"
        region_name = "us-east-1"

        #Launcing the AWS session
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=region_name)

        try:
            response = client.get_secret_value(SecretId=secret_name)
            secret = json.loads(response["SecretString"])
            return secret["CLIENT_ID"], secret["CLIENT_SECRET"]
        except Exception as e:
            print(f"Error retrieving secret: {e}")
            return None, None

#Initializing the Amadeus API
CLIENT_ID, CLIENT_SECRET = get_amadeus_api_keys()
amadeus = Client(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("API key and secret not found")

#Function to retrieve city names using city code
def city_code_search(city_code):
        try:
            response = amadeus.reference_data.locations.get(keyword = city_code, subType = 'CITY')

            if not response.data:
                return f"No city found for '{city_code}'"

            return response.data[0]['iataCode']

        except ResponseError as City_Code_Error:
            raise City_Code_Error

# #Flight Offers Search
def flight_offers(originlocationcode, destinationlocationcode, adults, departuredate, returndate):
    if not all((originlocationcode, destinationlocationcode, adults, departuredate, returndate)):
        print("All fields must be completed")
        return None
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=originlocationcode,
            destinationLocationCode=destinationlocationcode,
            adults=adults,
            departureDate=departuredate,
            returnDate=returndate
        )
        return response.data
    except ResponseError as Flight_Offers_Error:
        print(f"An error occurred: {Flight_Offers_Error}")
        return None
#
# #Get Flight Offers wrapper
def get_flight_offers(originlocation, destinationlocation, no_of_adults, departdate, returndate):
    try:
        origin_city_code = city_code_search(originlocation)
        if not origin_city_code:
            return json.dumps({"error": "Origin city code not found"})

        destination_city_code = city_code_search(destinationlocation)
        if not destination_city_code:
            return json.dumps({"error": "City Code not found"})

        flights_on_offer = flight_offers(origin_city_code,destination_city_code,no_of_adults, departdate, returndate)
        if not flights_on_offer:
            return json.dumps({"error": "No flight offers found"})

        return json.dumps(flights_on_offer)
    except ResponseError as e:
        return json.dumps({"error": str(e)})
#

def lambda_handler(event, context):
    try:
        # Extract parameters from event
        origin = event.get('originlocation')
        destination = event.get('destinationlocation')
        adults = event.get('no_of_adults')
        depart_date = event.get('departdate')
        return_date = event.get('returndate')

        # Get flight offers
        flight_results = get_flight_offers(
            origin, destination, adults, depart_date, return_date
        )

        # Return direct response
        return flight_results
    except Exception as e:
        return e





