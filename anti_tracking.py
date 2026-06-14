"""Strategy 4: Anti-Tracking to prevent price inflation"""

import random
import time
from fake_useragent import UserAgent


class AntiTracking:
    def __init__(self):
        try:
            self.ua = UserAgent()
        except:
            self.ua = None

    def get_random_headers(self):
        ua = self.ua.random if self.ua else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        return {
            "User-Agent": ua,
            "Accept-Language": random.choice([
                "en-US,en;q=0.9",
                "en-IN,en;q=0.9,hi;q=0.8",
                "en-GB,en;q=0.9",
            ]),
            "DNT": "1",
        }

    def get_serpapi_params(self):
        """Fresh search params - no cached/tracked results."""
        return {
            "no_cache": "true",
            "gl": random.choice(["in", "us", "uk"]),
            "hl": "en",
        }

    def random_delay(self, min_sec=1.5, max_sec=5.0):
        """Random delay to appear human."""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
        return delay
