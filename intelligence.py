import math
from datetime import datetime

class FlightScorer:
    """
    Score flight segments out of 100 based on price, stops, duration, and convenience.
    """
    WEIGHTS = {
        'price': 0.40,
        'duration': 0.25,
        'stops': 0.20,
        'airline': 0.15
    }

    AIRLINE_RATINGS = {
        'Singapore Airlines': 9.2,
        'Emirates': 8.8,
        'Qatar Airways': 8.9,
        'ANA': 9.0,
        'Lufthansa': 8.1,
        'Air India': 6.5,
        'IndiGo': 7.2,
        'SpiceJet': 5.8,
        'Vistara': 8.0,
        'AirAsia': 6.2
    }

    def score_flight(self, origin, destination, price, duration_minutes, stops, airline, route_avg=None):
        scores = {}
        
        # 1. Price Score: Lower is better
        if price is None:
            scores['price'] = 0.50  # Neutral price score
        elif route_avg:
            # Score is higher if price is lower than average
            ratio = price / route_avg
            scores['price'] = max(0.0, min(1.0, 1.2 - ratio))
        else:
            # Fallback if no average exists yet
            scores['price'] = 0.70

        # 2. Duration Score: Ideal is direct flight duration. We estimate based on stops.
        # Short durations are scored closer to 1.0.
        base_dur = 180 if stops == 0 else 360
        scores['duration'] = max(0.1, min(1.0, base_dur / max(1.0, duration_minutes)))

        # 3. Stops Score
        if stops == 0:
            scores['stops'] = 1.0
        elif stops == 1:
            scores['stops'] = 0.7
        else:
            scores['stops'] = 0.3

        # 4. Airline Rating Score
        rating = self.AIRLINE_RATINGS.get(airline, 7.0)
        scores['airline'] = rating / 10.0

        # Compute weighted average
        final_score = sum(scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS) * 100
        
        # Determine descriptive label
        if final_score >= 85:
            label = "Excellent Deal"
        elif final_score >= 70:
            label = "Good Deal"
        elif final_score >= 55:
            label = "Fair Deal"
        else:
            label = "Poor Value"

        return {
            'score': round(final_score),
            'label': label,
            'breakdown': {k: round(v * 100) for k, v in scores.items()}
        }


class PricePredictor:
    """
    Predict flight pricing behavior using offline route history.
    """
    def predict(self, db, origin, dest, depart_date, current_price):
        if current_price is None:
            return {
                'action': 'UNPRICED',
                'confidence': 0,
                'reason': 'No current price is available for this flight. Please check the booking link directly.',
                'percentile': None,
                'historical_avg': None,
                'historical_min': None,
                'predicted_range_min': None,
                'predicted_range_max': None
            }

        history = db.get_all_prices(origin, dest)
        prices = [h['price'] for h in history if h['price'] is not None]
        
        if len(prices) < 3:
            return {
                'action': 'COLLECTING DATA',
                'confidence': 50,
                'reason': 'Collecting historical data to build confidence intervals.',
                'percentile': 50,
                'historical_avg': current_price,
                'historical_min': current_price
            }

        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        # Compute Percentile
        below_count = sum(1 for p in prices if p < current_price)
        equal_count = sum(1 for p in prices if p == current_price)
        percentile = round(((below_count + 0.5 * equal_count) / len(prices)) * 100)

        # Volatility
        variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
        std_dev = math.sqrt(variance)
        volatility = std_dev / avg_price if avg_price > 0 else 0.1

        # Check recent trend slope (last 5 records)
        recent_prices = [h['price'] for h in history[-5:] if h['price'] is not None]
        if len(recent_prices) >= 3:
            trend_slope = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
        else:
            trend_slope = 0

        # Calculate days until departure
        try:
            dep_dt = datetime.strptime(depart_date, "%Y-%m-%d")
            days_out = (dep_dt - datetime.now()).days
        except:
            days_out = 30

        # Score decision signals
        confidence = 65
        if percentile <= 20:
            action = "BUY NOW"
            confidence += 15
            reason = f"Current rate is in the bottom {percentile}% of all historical logs. Highly recommended to book now."
        elif percentile >= 75:
            action = "WAIT"
            confidence += 10
            reason = f"Current price is higher than {percentile}% of historical points. A price dip is probable."
        else:
            if trend_slope < 0 and days_out > 21:
                action = "WAIT"
                reason = "Prices are trending downwards and departure is still several weeks away."
            elif days_out < 7:
                action = "BUY NOW"
                reason = "Departure is less than a week away. Last-minute tickets rarely drop further."
            else:
                action = "FAIR PRICE"
                reason = "Price is sitting near the route average. Set a Target alert to catch upcoming swings."

        return {
            'action': action,
            'confidence': min(95, max(40, confidence)),
            'reason': reason,
            'percentile': percentile,
            'historical_avg': round(avg_price),
            'historical_min': min_price,
            'predicted_range_min': round(current_price * (1 - volatility * 0.4)),
            'predicted_range_max': round(current_price * (1 + volatility * 0.4))
        }


class UserPreferences:
    """
    Applies custom blacklist and quality filters.
    """
    def __init__(self, blocked_airlines=None, max_stops=1):
        self.blocked_airlines = blocked_airlines or []
        self.max_stops = max_stops

    def filter_flights(self, flights):
        clean = []
        for f in flights:
            airline = f.get('airline', f.get('airlines', ['Unknown'])[0])
            if any(block.lower() in airline.lower() for block in self.blocked_airlines):
                continue
            if f.get('stops', 0) > self.max_stops:
                continue
            clean.append(f)
        return clean
