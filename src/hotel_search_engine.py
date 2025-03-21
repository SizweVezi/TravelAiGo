import json
import os
from datetime import datetime, date, timedelta
from amadeus import Client, ResponseError

amadeus = Client(
    client_id=os.environ.get("CLIENT_ID"),
    client_secret=os.environ.get("CLIENT_SECRET")
)

def lambda_handler(event, context):
    try:
        # Validate input parameters
        if not isinstance(event, dict):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid event format'})
            }

        location = event.get('location')
        check_in_date = event.get('check_in_date')
        check_out_date = event.get('check_out_date')

        # Validate required parameters
        if not location:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Location is required'})
            }

        # Convert string dates to date objects if provided
        if check_in_date:
            try:
                check_in_date = datetime.strptime(check_in_date, '%Y-%m-%d').date()
            except ValueError:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid check_in_date format. Use YYYY-MM-DD'})
                }
        else:
            check_in_date = date.today()

        if check_out_date:
            try:
                check_out_date = datetime.strptime(check_out_date, '%Y-%m-%d').date()
            except ValueError:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid check_out_date format. Use YYYY-MM-DD'})
                }
        else:
            check_out_date = check_in_date + timedelta(days=3)

        # Get hotel offers
        hotel_results = get_hotel_offers(location, check_in_date, check_out_date)

        # Return direct response
        return hotel_results
    except Exception as e:
        return json.dumps({'error': str(e)})


#City code function to retrieve city names by using city codes.
def city_code_search(city_name):
    try:
        response = amadeus.reference_data.locations.get(keyword=city_name, subType='CITY')
        return response.data[0]['address']['cityCode']
    except ResponseError as error:
        return str(error)

#Hotel city search. Fetches hotels by city code.
def hotel_city_search(cityCode):
    try:
        response = amadeus.reference_data.locations.hotels.by_city.get(cityCode=cityCode)
        hotel_names = [item['hotelId'] for item in response.data[:50]]
        return hotel_names

    except ResponseError as error:
        return str(error)

#Hotel offer search by hotelId check-in date and check-out date
def hotels_offers_search(hotelIds, checkInDate = date.today(), checkOutDate = date.today() + timedelta(days=3)):
    if not hotelIds:
        return []
    if checkInDate >= checkOutDate:
        raise ValueError("Check-in date must be before check-out date")
    try:
        response = amadeus.shopping.hotel_offers_search.get(
            hotelIds=hotelIds,
            checkInDate=checkInDate,
            checkOutDate=checkOutDate
        )
        return response.data
    except ResponseError as e:
        raise e

#Get hotel offers wrapper
def get_hotel_offers(location, check_in_date=date.today(), check_out_date=date.today() + timedelta(days=3)):
    """
    Search for hotel offers in a given location.

    Args:
        location: City name to search
        check_in_date: Check-in date (defaults to today)
        check_out_date: Check-out date (defaults to today + 3 days)

    Returns:
        JSON string containing hotel offers or error message
    """
    try:
        city_code = city_code_search(location)
        if not city_code:
            return json.dumps({"error": "City code not found"})

        hotel_ids = hotel_city_search(city_code)
        if not hotel_ids:
            return json.dumps({"error": "No hotels found"})

        hotel_offers = hotels_offers_search(hotel_ids, check_in_date, check_out_date)
        if not hotel_offers:
            return json.dumps({"error": "No offers found"})

        return json.dumps(hotel_offers)
    except Exception as e:
        return json.dumps({"error": str(e)})