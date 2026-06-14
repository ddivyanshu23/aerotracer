'''
Flight Price Checker Agent
All 5 strategies with dynamic base airport and flexible date ranges using fli.
'''

from datetime import datetime, timedelta
import calendar
import time

from config import Config
from database import FlightDB
from anti_tracking import AntiTracking
from notifier import Notifier

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


from intelligence import FlightScorer, PricePredictor


class FlightAgent:
    def __init__(self):
        self.db = FlightDB()
        self.anti = AntiTracking()
        self.notifier = Notifier()
        self.currency = Config.CURRENCY
        self.scorer = FlightScorer()
        self.predictor = PricePredictor()

    def parse_date_range(self, date_input):
        '''
        Parse flexible date input.
        
        Accepts:
            - "this month", "current month" → remaining days of current month
            - "next month"                  → entire next calendar month
            - "this and next month"         → remaining days + next month
            - Month name (e.g. "july", "aug", "september") → entire target month
            - Month + Year (e.g. "july 2026", "jul 26")
            - "2024-07" or "July 2024"      → entire month
            - "2024-07-01 to 2024-07-15"    → custom range
            - "2024-07-10"                  → single date (±3 days)
        '''
        import re
        date_input = date_input.strip().lower().replace("_", " ")
        # Normalize multiple spaces
        date_input = re.sub(r'\s+', ' ', date_input)
        
        today = datetime.now()
        
        # 1. Check for "this month" or "current month"
        if date_input in ["this month", "current month"]:
            start = today
            last_day = calendar.monthrange(today.year, today.month)[1]
            end = datetime(today.year, today.month, last_day)
            return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
            
        # 2. Check for "next month"
        if date_input == "next month":
            if today.month == 12:
                start = datetime(today.year + 1, 1, 1)
            else:
                start = datetime(today.year, today.month + 1, 1)
            last_day = calendar.monthrange(start.year, start.month)[1]
            end = datetime(start.year, start.month, last_day)
            return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
            
        # 3. Check for "this and next month", "current and next month", etc.
        if date_input in [
            "this and next month", "current and next month", 
            "this & next month", "current & next month",
            "this month and next month", "current month and next month"
        ]:
            start = today
            if today.month == 12:
                next_m = datetime(today.year + 1, 1, 1)
            else:
                next_m = datetime(today.year, today.month + 1, 1)
            last_day = calendar.monthrange(next_m.year, next_m.month)[1]
            end = datetime(next_m.year, next_m.month, last_day)
            return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

        # 4. Check for month names (e.g. "july", "july 2026", "july 26", "jul 26")
        months_map = {
            "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
            "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12
        }
        
        # Matches e.g. "july", "july 2026", "july 26", "july-2026"
        month_match = re.match(r'^([a-z]+)(?:\s+|-)?(\d{2,4})?$', date_input)
        if month_match:
            month_str = month_match.group(1)
            year_str = month_match.group(2)
            
            if month_str in months_map:
                target_month = months_map[month_str]
                if year_str:
                    target_year = int(year_str)
                    if target_year < 100:  # 2-digit year
                        target_year += 2000
                else:
                    # Default to current or next year
                    if target_month >= today.month:
                        target_year = today.year
                    else:
                        target_year = today.year + 1
                
                start = datetime(target_year, target_month, 1)
                last_day = calendar.monthrange(target_year, target_month)[1]
                end = datetime(target_year, target_month, last_day)
                
                if start < today:
                    start = today
                return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

        # 5. Standard date range: YYYY-MM-DD to YYYY-MM-DD
        if " to " in date_input:
            parts = date_input.split(" to ")
            return parts[0].strip(), parts[1].strip()

        if "," in date_input:
            parts = date_input.split(",")
            return parts[0].strip(), parts[1].strip()

        # 6. Year-Month format (YYYY-MM)
        ym_match = re.match(r'^(\d{4})-(\d{2})$', date_input)
        if ym_match:
            try:
                year = int(ym_match.group(1))
                month = int(ym_match.group(2))
                start = datetime(year, month, 1)
                if start < today:
                    start = today
                last_day = calendar.monthrange(year, month)[1]
                end = datetime(year, month, last_day)
                return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
            except:
                pass

        # 7. Single date YYYY-MM-DD -> ±3 days
        try:
            single = datetime.strptime(date_input, "%Y-%m-%d")
            start = single - timedelta(days=3)
            if start < today:
                start = today
            end = single + timedelta(days=3)
            return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        except:
            pass

        raise ValueError(f"Cannot parse date input: '{date_input}'")

    def generate_date_pairs(self, start_date, end_date, trip_duration_days=7, sample_interval=2):
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        if isinstance(trip_duration_days, int):
            durations = [trip_duration_days]
        else:
            durations = trip_duration_days

        pairs = []
        current = start

        while current <= end:
            for duration in durations:
                ret = current + timedelta(days=duration)
                if ret <= end + timedelta(days=max(durations)):
                    pairs.append((
                        current.strftime("%Y-%m-%d"),
                        ret.strftime("%Y-%m-%d")
                    ))
            current += timedelta(days=sample_interval)

        return pairs

    def _query_flights(self, origin, destination, dep_date, ret_date=None, cabin_class="ECONOMY", stops_limit="ANY", adults=1):
        try:
            origin_airport = resolve_airport(origin)
            destination_airport = resolve_airport(destination)
            seat_type = parse_cabin_class(cabin_class)
            stops = parse_max_stops(stops_limit)
            
            segments, trip_type = build_flight_segments(
                origin=origin_airport,
                destination=destination_airport,
                departure_date=dep_date,
                return_date=ret_date,
            )

            filters = FlightSearchFilters(
                trip_type=trip_type,
                passenger_info=PassengerInfo(adults=int(adults)),
                flight_segments=segments,
                stops=stops,
                seat_type=seat_type,
                sort_by=parse_sort_by("CHEAPEST"),
                show_all_results=True,
            )

            search_client = SearchFlights()
            results = search_client.search(
                filters,
                currency=self.currency
            )
            return results or []
        except Exception as e:
            print(f"      ⚠️ Search failed: {e}")
            return []

    def _parse_fli_result(self, res):
        if isinstance(res, tuple):
            price = res[0].price
            airline = " / ".join(filter(None, [r.primary_airline_name for r in res]))
            stops = max(r.stops for r in res)
            duration = sum(r.duration for r in res)
            return price, airline, stops, duration
        else:
            price = res.price
            airline = res.primary_airline_name or "Unknown"
            stops = res.stops
            duration = res.duration
            return price, airline, stops, duration

    def explore(self, origin, date_range, trip_duration=7, regions=None, budget=None):
        '''Strategy 1: Find cheapest destinations'''
        start_date, end_date = self.parse_date_range(date_range)

        mid_date = datetime.strptime(start_date, "%Y-%m-%d") + \
                   (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")) / 2
        dep = mid_date.strftime("%Y-%m-%d")

        durations = [trip_duration] if isinstance(trip_duration, int) else trip_duration

        if regions:
            destinations = []
            for r in regions:
                destinations.extend(Config.DESTINATIONS.get(r, []))
        else:
            destinations = []
            for dests in Config.DESTINATIONS.values():
                destinations.extend(dests)

        print(f'''
╔══════════════════════════════════════════════════════════════╗
║  🌍 STRATEGY 1: EXPLORE MODE                                ║
╠══════════════════════════════════════════════════════════════╣
║  From: {origin:<10}                                          ║
║  Date Range: {start_date} → {end_date:<27}║
║  Trip Durations: {durations} days                                    ║
║  Scanning: {len(destinations)} destinations                            ║
╚══════════════════════════════════════════════════════════════╝
        ''')

        results = []
        symbol = "₹" if self.currency == "INR" else "$"

        for i, dest in enumerate(destinations):
            if dest == origin:
                continue

            print(f"   [{i+1}/{len(destinations)}] Scanning {origin} ➔ {dest}...")
            best_price = None
            best_flight = None
            best_duration_day = None

            for dur in durations:
                ret = (mid_date + timedelta(days=dur)).strftime("%Y-%m-%d")
                try:
                    self.anti.random_delay(0.5, 1.5)
                    flights = self._query_flights(origin, dest, dep, ret, stops_limit=str(Config.MAX_STOPS))
                    
                    for res in flights:
                        price, airline, stops, duration = self._parse_fli_result(res)
                        if price and (best_price is None or price < best_price):
                            best_price = price
                            best_flight = (airline, stops, duration, ret, dur)
                except Exception as e:
                    print(f"   [{i+1}/{len(destinations)}] {origin}→{dest} (dur {dur}): ⚠️ {e}")
                    continue

            if best_price:
                if budget and best_price > budget:
                    continue

                airline, stops, duration, ret_date, final_dur = best_flight
                results.append({
                    "destination": dest,
                    "price": best_price,
                    "airline": airline,
                    "stops": stops,
                    "duration": duration,
                    "trip_duration": final_dur,
                })

                self.db.save_price(origin, dest, dep, ret_date, best_price, airline, stops, duration)
                print(f"   [{i+1}/{len(destinations)}] {origin}→{dest}: {symbol}{best_price:,.0f} (duration: {final_dur}d)")

        results.sort(key=lambda x: x["price"])

        print(f"\n{'═'*60}")
        print(f"🏆 TOP 15 CHEAPEST FROM {origin}:")
        print(f"{'═'*60}")

        for i, r in enumerate(results[:15], 1):
            print(f"  {i:>2}. {r['destination']:<5} — {symbol}{r['price']:>8,.0f}  |  {r['airline']:<20} (dur: {r['trip_duration']}d)")

        return results


    def search(self, origin, destination, date_range, trip_duration=7, travel_class=1, cabin_class="ECONOMY", stops_limit="ANY", adults=1):
        '''Strategy 2: Smart filtered search'''
        start_date, end_date = self.parse_date_range(date_range)
        date_pairs = self.generate_date_pairs(start_date, end_date, trip_duration, sample_interval=3)

        print(f'''
╔══════════════════════════════════════════════════════════════╗
║  🔍 STRATEGY 2: SMART FILTERED SEARCH                       ║
╠══════════════════════════════════════════════════════════════╣
║  {origin} → {destination:<10}                                         ║
║  Checking: {len(date_pairs)} date combinations                        ║
╚══════════════════════════════════════════════════════════════╝
        ''')

        all_flights = []
        rejected_count = 0
        no_price_count = 0
        symbol = "₹" if self.currency == "INR" else "$"

        if isinstance(travel_class, int):
            class_map = {1: "ECONOMY", 2: "PREMIUM_ECONOMY", 3: "BUSINESS", 4: "FIRST"}
            cabin = class_map.get(travel_class, cabin_class)
        else:
            cabin = travel_class or cabin_class

        for i, (dep, ret) in enumerate(date_pairs):
            try:
                print(f"   [{i+1}/{len(date_pairs)}] Scanning {dep}...")
                self.anti.random_delay(1.5, 4.0)
                flights = self._query_flights(origin, destination, dep, ret, cabin, stops_limit, adults)

                for res in flights:
                    price, airline, stops, duration = self._parse_fli_result(res)
                    if price is None:
                        no_price_count += 1
                    elif not price:
                        continue

                    is_budget = any(
                        budget.lower() in airline.lower()
                        for budget in Config.BUDGET_CARRIERS_TO_EXCLUDE
                    )
                    if is_budget:
                        rejected_count += 1
                        continue

                    layover_ok = True
                    if stops > 0:
                        all_layovers = []
                        if isinstance(res, tuple):
                            for segment in res:
                                if segment.layovers:
                                    all_layovers.extend(segment.layovers)
                        else:
                            if res.layovers:
                                all_layovers.extend(res.layovers)
                        
                        for l in all_layovers:
                            if hasattr(l, 'duration'):
                                ldur = l.duration
                                if ldur < Config.MIN_LAYOVER_MINUTES or ldur > Config.MAX_LAYOVER_MINUTES:
                                    layover_ok = False
                                    rejected_count += 1
                                    break
                    
                    if not layover_ok:
                        continue

                    all_flights.append({
                        "price": price,
                        "departure_date": dep,
                        "return_date": ret,
                        "departure_day": datetime.strptime(dep, "%Y-%m-%d").strftime("%a"),
                        "airlines": [airline],
                        "stops": stops,
                        "duration": duration,
                    })

                    self.db.save_price(
                        origin, destination, dep, ret, price,
                        airline, stops, duration
                    )

            except Exception as e:
                print(f"   [{i+1}/{len(date_pairs)}] {dep}: ⚠️ {e}")
                continue

        # Fetch route average from historical logs
        route_avg = self.db.get_route_average(origin, destination)

        # Apply scoring and prediction metrics to each flight
        for f in all_flights:
            # 1. Quality Score
            score_data = self.scorer.score_flight(
                origin=origin,
                destination=destination,
                price=f['price'],
                duration_minutes=f['duration'],
                stops=f['stops'],
                airline=f['airlines'][0],
                route_avg=route_avg
            )
            f['score_data'] = score_data

            # 2. Predictive recommendation
            predict_data = self.predictor.predict(
                db=self.db,
                origin=origin,
                dest=destination,
                depart_date=f['departure_date'],
                current_price=f['price']
            )
            f['prediction'] = predict_data

        # Sort by value score descending by default
        all_flights.sort(key=lambda x: x['score_data']['score'], reverse=True)

        print(f"\n{'═'*65}")
        print(f"  🚫 Rejected: {rejected_count} junk flights")
        print(f"  ✅ Quality flights: {len(all_flights)}")
        if no_price_count > 0:
            print(f"  ⚠️  Omitted: {no_price_count} flights with unpriced/missing fares")
            print(f"      (Common for restricted/seasonal destinations like Leh - IXL)")
        print(f"{'═'*65}\n")

        for i, f in enumerate(all_flights[:20], 1):
            price_str = f"{symbol}{f['price']:>8,.0f}" if f['price'] is not None else "Check Fare"
            print(f"  {i:>2}. {price_str}  |  {f['departure_date']} → {f['return_date']}  |  Score: {f['score_data']['score']}/100 ({f['score_data']['label']})")
            print(f"      {', '.join(f['airlines'])}  |  Rec: {f['prediction']['action']} ({f['prediction']['confidence']}% confidence)")

        return all_flights

    def date_grid(self, origin, destination, date_range, trip_durations=None):
        '''Strategy 3: Full date grid scan'''
        if trip_durations is None:
            trip_durations = [7]

        start_date, end_date = self.parse_date_range(date_range)
        date_pairs = self.generate_date_pairs(start_date, end_date, trip_durations, sample_interval=1)

        print(f'''
╔══════════════════════════════════════════════════════════════╗
║  📅 STRATEGY 3: DATE GRID SCANNER                           ║
╠══════════════════════════════════════════════════════════════╣
║  {origin} → {destination:<10}                                         ║
║  Total combinations: {len(date_pairs):<5}                              ║
╚══════════════════════════════════════════════════════════════╝
        ''')

        grid_results = []
        symbol = "₹" if self.currency == "INR" else "$"

        for i, (dep, ret) in enumerate(date_pairs):
            try:
                print(f"   [{i+1}/{len(date_pairs)}] Scanning {dep}...")
                self.anti.random_delay(1.5, 3.5)
                flights = self._query_flights(origin, destination, dep, ret, stops_limit=str(Config.MAX_STOPS))

                best_price = None
                best_airline = "Unknown"

                for res in flights:
                    price, airline, stops, duration = self._parse_fli_result(res)
                    if price and (best_price is None or price < best_price):
                        best_price = price
                        best_airline = airline

                if best_price:
                    dep_day = datetime.strptime(dep, "%Y-%m-%d").strftime("%a")
                    trip_len = (datetime.strptime(ret, "%Y-%m-%d") - datetime.strptime(dep, "%Y-%m-%d")).days

                    grid_results.append({
                        "departure_date": dep,
                        "return_date": ret,
                        "departure_day": dep_day,
                        "trip_days": trip_len,
                        "price": best_price,
                        "airline": best_airline
                    })

                    print(f"   [{i+1}/{len(date_pairs)}] {dep} ({dep_day}): {symbol}{best_price:,.0f}")

            except Exception as e:
                print(f"   [{i+1}/{len(date_pairs)}] {dep}: ⚠️ {e}")
                continue

        grid_results.sort(key=lambda x: x["price"])

        if grid_results:
            cheapest = grid_results[0]
            print(f"\n{'═'*65}")
            print(f"  🏆 CHEAPEST: {symbol}{cheapest['price']:,.0f}")
            print(f"     {cheapest['departure_date']} ({cheapest['departure_day']}) → {cheapest['return_date']}")
            print(f"{'═'*65}")

        return grid_results

    def set_alert(self, origin, destination, date_range, trip_duration=7, target_price=None):
        '''Strategy 5: Set price alert'''
        start_date, end_date = self.parse_date_range(date_range)

        if target_price is None:
            print(f"\n   🔍 Auto-calculating target price...")
            mid = datetime.strptime(start_date, "%Y-%m-%d") + \
                  (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")) / 2
            dep = mid.strftime("%Y-%m-%d")
            ret = (mid + timedelta(days=trip_duration)).strftime("%Y-%m-%d")

            try:
                flights = self._query_flights(origin, destination, dep, ret, stops_limit=str(Config.MAX_STOPS))
                current_price = None
                if flights:
                    price, airline, stops, duration = self._parse_fli_result(flights[0])
                    current_price = price

                if current_price:
                    target_price = int(current_price * 0.75)
                else:
                    print("   ⚠️ Provide --target manually")
                    return None

            except Exception as e:
                print(f"   ⚠️ Error: {e}")
                return None

        alert_id = self.db.create_alert(
            origin, destination, start_date, end_date, trip_duration, target_price
        )

        symbol = "₹" if self.currency == "INR" else "$"
        print(f'''
╔══════════════════════════════════════════════════════════════╗
║  🔔 PRICE ALERT SET! (ID: #{alert_id})                        ║
╠══════════════════════════════════════════════════════════════╣
║  Route: {origin} → {destination}                                    ║
║  Target: {symbol}{target_price:,.0f}                                        ║
║  Status: ✅ ACTIVE                                            ║
╚══════════════════════════════════════════════════════════════╝
        ''')

        return alert_id

    def check_alerts(self):
        '''Check all active alerts'''
        alerts = self.db.get_active_alerts()

        if not alerts:
            print("   No active alerts.")
            return []

        print(f"\n🔍 Checking {len(alerts)} alert(s)...\n")
        triggered = []
        symbol = "₹" if self.currency == "INR" else "$"

        for alert in alerts:
            alert_id = alert[0]
            origin = alert[1]
            destination = alert[2]
            date_start = alert[3]
            date_end = alert[4]
            trip_duration = alert[5]
            target_price = alert[6]

            date_pairs = self.generate_date_pairs(date_start, date_end, trip_duration, sample_interval=3)

            best_price = None
            best_dep = None
            best_ret = None
            best_airline = None

            for dep, ret in date_pairs[:5]:
                try:
                    self.anti.random_delay(2.0, 5.0)
                    flights = self._query_flights(origin, destination, dep, ret, stops_limit=str(Config.MAX_STOPS))

                    for res in flights:
                        price, airline, stops, duration = self._parse_fli_result(res)
                        if price and (best_price is None or price < best_price):
                            best_price = price
                            best_dep = dep
                            best_ret = ret
                            best_airline = airline

                except:
                    continue

            if best_price:
                self.db.update_alert_best(alert_id, best_price, best_dep)

                if best_price <= target_price:
                    self.db.trigger_alert(alert_id, best_price, best_dep)
                    triggered.append({
                        "alert_id": alert_id,
                        "origin": origin,
                        "destination": destination,
                        "price": best_price,
                        "target": target_price,
                        "departure": best_dep,
                        "return": best_ret,
                        "airline": best_airline
                    })

                    print(f"   🚨 ALERT #{alert_id} TRIGGERED!")
                    print(f"      {origin}→{destination}: {symbol}{best_price:,.0f}")

                    self.notifier.notify_deal(
                        origin, destination, best_price,
                        best_dep, best_ret, best_airline, target_price
                    )
                else:
                    print(f"   ⏳ Alert #{alert_id}: {symbol}{best_price:,.0f} (target: {symbol}{target_price:,.0f})")

        return triggered

    def full_analysis(self, origin, destination, date_range, trip_duration=7):
        '''Run all strategies'''
        print(f'''
╔══════════════════════════════════════════════════════════════════╗
║          ✈️  FULL ANALYSIS - ALL STRATEGIES  ✈️                   ║
╠══════════════════════════════════════════════════════════════════╣
║  {origin} → {destination}                                                ║
╚══════════════════════════════════════════════════════════════════╝
        ''')

        results = {}
        results["search"] = self.search(origin, destination, date_range, trip_duration)
        results["date_grid"] = self.date_grid(origin, destination, date_range, [trip_duration])

        return results

    def flexible_search(self, origin, destination, date_start, date_end, min_days, max_days, budget=None, cabin_class="ECONOMY", stops_limit="ANY", adults=1):
        """
        Scan flights within a flexible date window and variable durations, scoring results.
        """
        # Convert date range or months to dates
        start_date, end_date = self.parse_date_range(f"{date_start} to {date_end}")
        durations = list(range(int(min_days), int(max_days) + 1))
        
        # Sample date pairs to avoid heavy rate limits
        date_pairs = self.generate_date_pairs(start_date, end_date, durations, sample_interval=4)

        print(f"\n🔍 Flexible Search: {origin} → {destination} ({len(date_pairs)} combinations)\n")
        results = []
        symbol = "₹" if self.currency == "INR" else "$"

        for i, (dep, ret) in enumerate(date_pairs[:15]): # Limit to top 15 queries to avoid IP ban
            try:
                print(f"   [{i+1}/{min(15, len(date_pairs))}] Scanning {dep}...")
                self.anti.random_delay(1.5, 3.5)
                flights = self._query_flights(origin, destination, dep, ret, cabin_class, stops_limit, adults)
                
                for res in flights:
                    price, airline, stops, duration = self._parse_fli_result(res)
                    if price is None:
                        pass
                    elif not price:
                        continue
                    if price is not None and budget and price > budget:
                        continue
                        
                    # Quality Score
                    route_avg = self.db.get_route_average(origin, destination)
                    score_data = self.scorer.score_flight(
                        origin=origin,
                        destination=destination,
                        price=price,
                        duration_minutes=duration,
                        stops=stops,
                        airline=airline,
                        route_avg=route_avg
                    )
                    
                    # Prediction
                    pred = self.predictor.predict(self.db, origin, destination, dep, price)

                    results.append({
                        "price": price,
                        "departure_date": dep,
                        "return_date": ret,
                        "departure_day": datetime.strptime(dep, "%Y-%m-%d").strftime("%a"),
                        "airlines": [airline],
                        "stops": stops,
                        "duration": duration,
                        "score_data": score_data,
                        "prediction": pred
                    })
                    
                    # Save to DB
                    self.db.save_price(origin, destination, dep, ret, price, airline, stops, duration)

            except Exception as e:
                print(f"   [{i+1}/{len(date_pairs)}] {dep}: ⚠️ {e}")
                continue

        # Sort by value score descending
        results.sort(key=lambda x: x['score_data']['score'], reverse=True)
        return results[:20]

    def search_with_nearby(self, origin, destination, date_start, date_end, trip_duration=7, cabin_class="ECONOMY", stops_limit="ANY", adults=1):
        """
        Query primary route and compare prices against nearby alternate departure airports.
        """
        NEARBY_AIRPORTS = {
            'BLR': ['MAA', 'HYD', 'GOI'],      # Bengaluru: Chennai, Hyderabad, Goa
            'DEL': ['JAI', 'LKO', 'AMD'],      # Delhi: Jaipur, Lucknow, Ahmedabad
            'BOM': ['PNQ', 'GOI', 'AMD'],      # Mumbai: Pune, Goa, Ahmedabad
            'LKO': ['DEL', 'JAI'],             # Lucknow: Delhi, Jaipur
            'LHR': ['LGW', 'STN', 'LTN']       # London: Gatwick, Stansted, Luton
        }

        # Run primary search
        print(f"\n✈️ Searching primary route: {origin} → {destination}...")
        primary_results = self.search(origin, destination, f"{date_start} to {date_end}", trip_duration, cabin_class=cabin_class, stops_limit=stops_limit, adults=adults)
        
        comparison = {
            "primary": primary_results,
            "alternatives": []
        }

        # Check alternate airports
        alternatives = NEARBY_AIRPORTS.get(origin.upper(), [])
        for alt in alternatives:
            print(f"✈️ Scanning alternative departure: {alt} → {destination}...")
            try:
                self.anti.random_delay(1.5, 3.5)
                # Just fetch the cheapest flight for alt route to minimize rate-limiting
                alt_flights = self.search(alt, destination, f"{date_start} to {date_end}", trip_duration, cabin_class=cabin_class, stops_limit=stops_limit, adults=adults)
                if alt_flights:
                    valid_alt_flights = [af for af in alt_flights if af['price'] is not None]
                    if valid_alt_flights:
                        cheapest_alt = min(valid_alt_flights, key=lambda x: x['price'])
                        
                        # Compute savings
                        if primary_results:
                            valid_primary_results = [pf for pf in primary_results if pf['price'] is not None]
                            if valid_primary_results:
                                cheapest_prim = min(valid_primary_results, key=lambda x: x['price'])
                                savings = cheapest_prim['price'] - cheapest_alt['price']
                            else:
                                savings = 0
                        else:
                            savings = 0
                            
                        comparison["alternatives"].append({
                            "origin": alt,
                            "price": cheapest_alt['price'],
                            "savings": savings,
                            "departure_date": cheapest_alt['departure_date'],
                            "return_date": cheapest_alt['return_date'],
                            "airline": cheapest_alt['airlines'][0]
                        })
            except Exception as e:
                print(f"   Alternative {alt} scan failed: {e}")
                continue

        return comparison
