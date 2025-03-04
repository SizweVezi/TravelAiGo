import os
from dotenv import load_dotenv, find_dotenv
from amadeus import ResponseError, Client

_ = load_dotenv(find_dotenv()) # read local .env file
#Amadeus
amadeus = Client(
        client_id = os.environ.get("api_key"),
        client_secret = os.environ.get("api_secret")
    )

# Creates a traveller profile with personal and contact information, returns the information in a dictionary
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

 # USAGE:: Creating a traveller
john = create_traveller(
    traveller_id=1,
    first_name="John",
    last_name="Doe",
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
        #  amazonq-ignore-next-line
        'holder': True
    }
)

#Flight offers search
def flight_offers(originlocationcode, destinationlocationcode, adults, departuredate, returndate):
    logger.info(f"Searching flight offers: {originlocationcode} to {destinationlocationcode}, {adults} adults, departure: {departuredate}, return: {returndate}")
    try:
          response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=originlocationcode,
            destinationLocationCode=destinationlocationcode,
            adults=adults,
            departureDate=departuredate,
            returnDate=returndate
        )
        logger.info(f"Successfully retrieved {len(response.data)} flight offers")
        return True, response.data
    except ResponseError as error:
        logger.error(f"Error in flight_offers search: {str(error)}")
        return False, str(error)


try:
    # USAGE:: Flight Offers Search to find the cheapest flights
    flight_search = flight_offers(
        'SYD',
        'BKK',
        1,
        '2023-10-01',
        '2023-10-08')

    #Flight Offers Price to confirm the price of the chosen flight
    price_confirmation = amadeus.shopping.flight_offers.pricing.post(
       flight_search[0]).data

    #Flight create orders to book the flight
    flight_order = amadeus.booking.flight_orders.post(
       flight_search[0], john).data

except ResponseError as api_error:
    logger.error(f"Amadeus API error: {str(api_error)}")
    raise api_error
