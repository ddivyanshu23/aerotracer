import sqlite3
from datetime import datetime
from config import Config


class FlightDB:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_PATH, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin TEXT,
                destination TEXT,
                departure_date TEXT,
                return_date TEXT,
                price REAL,
                currency TEXT,
                airline TEXT,
                stops INTEGER,
                duration_minutes INTEGER,
                via TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin TEXT,
                destination TEXT,
                departure_date_start TEXT,
                departure_date_end TEXT,
                trip_duration_days INTEGER,
                target_price REAL,
                currency TEXT DEFAULT 'INR',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                triggered_at TIMESTAMP,
                best_price_found REAL,
                best_date_found TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin TEXT,
                destination TEXT,
                departure_date TEXT,
                return_date TEXT,
                price REAL,
                currency TEXT,
                airline TEXT,
                stops INTEGER,
                duration_minutes INTEGER,
                layover_info TEXT,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    def save_price(self, origin, destination, departure_date, return_date,
                   price, airline, stops, duration, via=""):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO price_history 
            (origin, destination, departure_date, return_date, price, currency, airline, stops, duration_minutes, via)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (origin, destination, departure_date, return_date, price, Config.CURRENCY, airline, stops, duration, via))
        self.conn.commit()

    def get_lowest_price(self, origin, destination):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT MIN(price), departure_date, return_date, airline 
            FROM price_history
            WHERE origin=? AND destination=?
        ''', (origin, destination))
        return cursor.fetchone()

    def get_price_history(self, origin, destination, departure_date=None, return_date=None):
        cursor = self.conn.cursor()
        if departure_date and return_date:
            cursor.execute('''
                SELECT price, airline, stops, checked_at FROM price_history
                WHERE origin=? AND destination=? AND departure_date=? AND return_date=?
                ORDER BY checked_at DESC LIMIT 30
            ''', (origin, destination, departure_date, return_date))
        else:
            cursor.execute('''
                SELECT price, airline, departure_date, return_date, checked_at 
                FROM price_history
                WHERE origin=? AND destination=?
                ORDER BY checked_at DESC LIMIT 50
            ''', (origin, destination))
        return cursor.fetchall()

    def create_alert(self, origin, destination, date_start, date_end,
                     trip_duration, target_price):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO alerts 
            (origin, destination, departure_date_start, departure_date_end, trip_duration_days, target_price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (origin, destination, date_start, date_end, trip_duration, target_price))
        self.conn.commit()
        return cursor.lastrowid

    def get_active_alerts(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM alerts WHERE is_active = 1")
        return cursor.fetchall()

    def trigger_alert(self, alert_id, best_price, best_date):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE alerts 
            SET is_active=0, triggered_at=?, best_price_found=?, best_date_found=?
            WHERE id=?
        ''', (datetime.now().isoformat(), best_price, best_date, alert_id))
        self.conn.commit()

    def update_alert_best(self, alert_id, price, date):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE alerts SET best_price_found=?, best_date_found=? WHERE id=?
        ''', (price, date, alert_id))
        self.conn.commit()

    def get_route_average(self, origin, destination):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT AVG(price) FROM price_history
            WHERE origin=? AND destination=?
        ''', (origin.upper(), destination.upper()))
        res = cursor.fetchone()
        return res[0] if res and res[0] is not None else None

    def get_all_prices(self, origin, destination):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT price, departure_date, return_date, checked_at FROM price_history
            WHERE origin=? AND destination=?
            ORDER BY checked_at ASC
        ''', (origin.upper(), destination.upper()))
        rows = cursor.fetchall()
        return [{'price': r[0], 'departure_date': r[1], 'return_date': r[2], 'checked_at': r[3]} for r in rows]

    def close(self):
        self.conn.close()
