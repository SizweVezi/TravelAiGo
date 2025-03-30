import os
import json
import boto3.session
from amadeus import Client,ResponseError
from boto3 import client
from hotel_search_engine import get_hotel_offers

# Load api secrets from secrets manager
def get_amadeus_api_keys():
    secret_name = "amadeus_secret"
    region_name = "us-east-1"

    session = boto3.session.Session()
    aws_client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        response = aws_client.get_secret_value(SecretId = secret_name)
        secret = json.loads(response['SecretString'])
        return secret['CLIENT_ID'], secret['CLIENT_SECRET']
    except Exception as e:
        print(f"Error retrieving secrets: {str(e)}")
        return None, None

# Initialize Amadeus API
try:
    CLIENT_ID, CLIENT_SECRET = get_amadeus_api_keys()
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("Access Keys Not Found")

    amadeus = Client(
        client_id = CLIENT_ID,
        client_secret = CLIENT_SECRET
    )
except Exception as e:
    print(f"Error initializing Amadeus client: {str(e)}")
    raise

#Function to define traveller details, returns them as a dict

def create_traveller(traveller_id, first_name, last_name, dob, gender, email,phone_number, country_code, document_info=None):
    traveller = {
        'id': traveller_id,
        'dateOfBirth': dob,
        'name': {
            'firstName': first_name,
            'lastName': last_name
        },
        'gender': gender,
        'contact': {
            'emailAddress': email,
            'phones': [{
                'deviceType': 'MOBILE',
                'countryCallingCode': country_code,
                'number': phone_number
            }]
        },
        'documents': []
    }
    if document_info:
        traveller['documents'].append(document_info)
    return traveller

# Create a traveller
guest = create_traveller(
        traveller_id=1,
        first_name="Sizwe",
        last_name="Vezi",
        dob="1970-01-01",
        gender="M",
        email="johndoe@example.com",
        phone_number="16505360797",
        country_code="1",
        document_info={
            'documentType': 'PASSPORT',
            'birthPlace': 'London',
            'issuanceLocation': 'London',
            'issuanceDate': '2015-03-06',
            'number': '00000000',
            'expiryDate': '2025-03-06',
            'issuanceCountry': 'GB',
            'validityCountry': 'GB',
            'nationality': 'GB',
            'holder': True
        }
    )


payment = [
    {
        "method": "creditCard",
        "card": {
            "vendorCode": "VI",
            "cardNumber": "4111111111111111",
            "expiryDate": "2026-01"
        }
    }
]

# Book hotel function
def book_hotel(hotel_offer_id, guests, payments):
    try:
        response = amadeus.booking.hotel_bookings.post(
            hotel_offer_id=hotel_offer_id,
            guests=guest,
            payments=payment
        )
        return response.data
    except Exception as e:
        return str(e)


def lambda_handler(event, context):
    hotel_offer_id = event.get("hotel_offer_id")
    guests = event.get("guest")
    payments = event.get("payments")

    try:
        booking = book_hotel(hotel_offer_id,guests,payments)
        return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Booking successful"
        })
    }
    except ResponseError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }