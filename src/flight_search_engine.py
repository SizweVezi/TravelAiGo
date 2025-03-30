import json
import os
import boto3
import logging
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
amadeus = Client(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, log_level='debug')
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


# Traveler Details
traveler = [
    {
        "id": "1",  # Must be a string
        "dateOfBirth": "1970-01-01",
        "name": {
            "firstName": "John",
            "lastName": "Doe"
        },
        "gender": "MALE",
        "contact": {
            "emailAddress": "johndoe@example.com",
            "phones": [
                {
                    "deviceType": "MOBILE",
                    "countryCallingCode": "1",
                    "number": "6505360797"
                }
            ]
        },
        "documents": [
            {
                "documentType": "PASSPORT",
                "birthPlace": "London",
                "issuanceLocation": "London",
                "issuanceDate": "2025-03-06",
                "number": "00000000",
                "expiryDate": "2035-03-06",
                "issuanceCountry": "GB",
                "validityCountry": "GB",
                "nationality": "GB",
                "holder": True
            }
        ]
    }
]



# #Flight Offers Search
def flight_search_offer(originLocationCode, destinationLocationCode, adults, departureDate, returnDate):
    if not all((originLocationCode, destinationLocationCode, adults, departureDate, returnDate)):
        print("All fields must be completed")
        return None
    try:
            response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=originLocationCode,
            destinationLocationCode=destinationLocationCode,
            adults=adults,
            departureDate=departureDate,
            returnDate=returnDate
        )
            return response.data
    except ResponseError as e:
        raise e
#
# #Get Flight Offers wrapper
def get_flight_offers(originLocationCode, destinationLocationCode, adults, departureDate, returnDate):
    try:
        origin_city_code = city_code_search(originLocationCode)
        if not origin_city_code:
            return json.dumps({"error": "Origin city code not found"})

        destination_city_code = city_code_search(destinationLocationCode)
        if not destination_city_code:
            return json.dumps({"error": "City Code not found"})

        flights_on_offer = flight_search_offer(originLocationCode, destinationLocationCode, adults, departureDate, returnDate)
        if not flights_on_offer:
            return json.dumps({"error": "No flight offers found"})

        return flights_on_offer
    except ResponseError as e:
        return e
#
# Searching for the specific flight with the travel details specified
search_flight_offer = get_flight_offers('NYC', 'BKK', 1, '2025-11-01',  '2025-11-03')
confirm_flight = search_flight_offer[0]

# Function to confirm the flight price offer
def price_confirm(offer):
    try:
        response = amadeus.shopping.flight_offers.pricing.post(offer)
        return response.data
    except ResponseError as e:
        raise e

# Function to book the flight
def book_flight(flight, travelers):
    try:
        response = amadeus.booking.flight_orders.post(
            flight=flight,
            travelers=travelers
        )
        return response.data
    except ResponseError as e:
        raise e

# flight booking
secure_flight = book_flight(confirm_flight, traveler)


def lambda_handler(event, context):
    try:
        # Extract parameters from event using correct parameter names
        originLocationCode = event.get('origin')
        destinationLocationCode = event.get('destination')
        adults = event.get('adults', 1)  # Default to 1 adult
        departureDate = event.get('departureDate')
        returnDate = event.get('returnDate')

        # Validate required parameters
        if not all([originLocationCode, destinationLocationCode, departureDate, returnDate]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameters'
                })
            }

        # Step 1: Search for flights
        flight_offers_response = get_flight_offers(
            originLocationCode,
            destinationLocationCode,
            adults,
            departureDate,
            returnDate
        )

        if not flight_offers_response:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'No flights found'
                })
            }

        # Step 2: Book the first flight offer
        selected_offer = flight_offers_response[0]
        booked_flight = book_flight(selected_offer, traveler)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'flightOffers': flight_offers_response,
                'bookingConfirmation': booked_flight
            }, indent=4)
        }

    except ResponseError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': str(e)
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }