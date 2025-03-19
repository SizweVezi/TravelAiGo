import unittest
import json
from unittest.mock import patch, MagicMock
from src.flight_search_engine import city_code_search, flight_offers, get_flight_offers

class TestFlightSearchEngine(unittest.TestCase):

    @patch('src.flight_search_engine.amadeus.reference_data.locations.get')
    def test_city_code_search(self, mock_get):
        # Mock the response
        mock_response = MagicMock()
        mock_response.data = [{'iataCode': 'LON'}]
        mock_get.return_value = mock_response

        # Test valid city code
        self.assertEqual(city_code_search('London'), 'LON')

        # Test invalid city code
        mock_response.data = []
        self.assertEqual(city_code_search('InvalidCity'), "No city found for 'InvalidCity'")

    @patch('src.flight_search_engine.amadeus.shopping.flight_offers_search.get')
    def test_flight_offers(self, mock_get):
        # Mock the response
        mock_response = MagicMock()
        mock_response.data = [{'offer': 'some_offer'}]
        mock_get.return_value = mock_response

        # Test valid flight offers
        self.assertEqual(flight_offers('LON', 'NYC', 1, '2025-06-23', '2025-07-26'), [{'offer': 'some_offer'}])

        # Test missing parameters
        self.assertIsNone(flight_offers('', 'NYC', 1, '2025-06-23', '2025-07-26'))

    @patch('src.flight_search_engine.city_code_search')
    @patch('src.flight_search_engine.flight_offers')
    def test_get_flight_offers(self, mock_flight_offers, mock_city_code_search):
        # Mock the city code search
        mock_city_code_search.side_effect = ['LON', 'NYC']

        # Mock the flight offers
        mock_flight_offers.return_value = [{'offer': 'some_offer'}]

        # Test valid flight offers
        result = get_flight_offers('London', 'New York', 1, '2025-06-23', '2025-07-26')
        self.assertEqual(result, json.dumps([{'offer': 'some_offer'}]))

        # Test city code not found
        mock_city_code_search.side_effect = [None, 'NYC']
        result = get_flight_offers('InvalidCity', 'New York', 1, '2025-06-23', '2025-07-26')
        self.assertEqual(result, json.dumps({"error": "Origin city code not found"}))

        # Test no flight offers found
        mock_city_code_search.side_effect = ['LON', 'NYC']
        mock_flight_offers.return_value = None
        result = get_flight_offers('London', 'New York', 1, '2025-06-23', '2025-07-26')
        self.assertEqual(result, json.dumps({"error": "No flight offers found"}))

if __name__ == '__main__':
    unittest.main()