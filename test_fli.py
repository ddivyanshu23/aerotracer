import os
import sys
from fli.core import (
    build_flight_segments,
    parse_cabin_class,
    parse_max_stops,
    parse_sort_by,
    resolve_airport,
)
from fli.models import (
    FlightSearchFilters,
    PassengerInfo,
)
from fli.search import SearchFlights

def test_search():
    print("Resolving airports...")
    origin_airport = resolve_airport("DEL")
    destination_airport = resolve_airport("BOM")
    seat_type = parse_cabin_class("ECONOMY")
    stops = parse_max_stops("1")
    
    print("Building segments...")
    segments, trip_type = build_flight_segments(
        origin=origin_airport,
        destination=destination_airport,
        departure_date="2026-08-15",
        return_date="2026-08-22",
    )

    print("Constructing filters...")
    filters = FlightSearchFilters(
        trip_type=trip_type,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=segments,
        stops=stops,
        seat_type=seat_type,
        sort_by=parse_sort_by("CHEAPEST"),
        show_all_results=True,
    )

    print("Searching...")
    search_client = SearchFlights()
    results = search_client.search(
        filters,
        currency="INR"
    )

    if not results:
        print("No flights found!")
        return

    print(f"Found {len(results)} flight options:")
    for res in results[:5]:
        # res is a tuple of FlightResult for round-trips
        # Let's extract total price
        if isinstance(res, tuple):
            print(f"Price: {res[0].price} {res[0].currency} | Airlines: {res[0].primary_airline_name} / {res[1].primary_airline_name if len(res) > 1 else ''} | Stops: {res[0].stops}")
        else:
            print(f"Price: {res.price} {res.currency} | Airline: {res.primary_airline_name} | Stops: {res.stops}")

if __name__ == "__main__":
    test_search()
