import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    CURRENCY = os.getenv("CURRENCY", "INR")
    CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", 60))

    # Notifications
    SMTP_EMAIL = os.getenv("SMTP_EMAIL")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # Strategy 2: Smart Filters
    BUDGET_CARRIERS_TO_EXCLUDE = [
        "SpiceJet", "Go First", "Alliance Air", "FlyBig", "Star Air",
        "Spirit", "Frontier", "Allegiant", "Ryanair", "Wizz Air", "EasyJet"
    ]

    MAX_STOPS = 1
    MIN_LAYOVER_MINUTES = 45
    MAX_LAYOVER_MINUTES = 360

    # Explore destinations pool
    DESTINATIONS = {
        "domestic_india": [
            "DEL", "BOM", "BLR", "HYD", "MAA", "CCU", "GOI",
            "JAI", "AMD", "PNQ", "COK", "SXR", "IXC", "GAU",
            "PAT", "VNS", "IXB", "RPR", "IDR", "NAG"
        ],
        "southeast_asia": [
            "BKK", "SIN", "KUL", "HAN", "SGN", "MNL", "CGK", "DPS"
        ],
        "middle_east": [
            "DXB", "DOH", "AUH", "MCT", "BAH", "RUH", "AMM"
        ],
        "east_asia": [
            "NRT", "HND", "ICN", "HKG", "PVG", "TPE"
        ],
        "europe": [
            "LHR", "CDG", "FRA", "AMS", "FCO", "BCN", "IST",
            "VIE", "ZRH", "MUC", "PRG", "BUD", "WAW", "ATH"
        ],
        "americas": [
            "JFK", "SFO", "LAX", "ORD", "YYZ", "EWR", "IAD"
        ],
        "oceania": [
            "SYD", "MEL", "AKL", "BNE"
        ],
        "africa": [
            "NBO", "CPT", "CAI", "ADD", "CMN"
        ],
        "south_asia": [
            "CMB", "KTM", "DAC", "MLE"
        ]
    }

    DB_PATH = "flights.db"
