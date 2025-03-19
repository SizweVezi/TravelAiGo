import src.flight_search_engine
from amadeus import Client, ResponseError
import os

amadeus = Client(
    client_id = os.environ.get("client_id"),
    client_secret = os.environ.get("client_secret")
        )

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

try:
#     # Create a traveller
    sizwe = create_traveller(
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
#
#
#     #flight search based on criteria
    flight_search = src.flight_search_engine.get_flight_offers(originlocation="",
    destinationlocation="",
    no_of_adults=0,
    departdate="",
    returndate="" )
#
#
#     #price confirmation from price search
    price_confirmation = amadeus.shopping.flight_offers.pricing.post(
        flight_search[0]).data
#
#     #Booking of actual flight
    flight_order = amadeus.booking.flight_orders.post(
        flight_search[0],sizwe).data
#
except ResponseError as api_error:
    raise api_error