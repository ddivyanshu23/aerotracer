import os
import sys
import uuid
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory

# Ensure we import correctly from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import io
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from flight_agent import FlightAgent
from database import FlightDB
from config import Config

app = Flask(__name__, static_folder='static', static_url_path='')

# Global dictionary to track background tasks
active_tasks = {}

def run_agent_search(task_id, task_type, params):
    agent = FlightAgent()
    try:
        active_tasks[task_id]['status'] = 'running'
        active_tasks[task_id]['logs'].append("Initializing flight search...")
        
        # Override printing to capture logs
        class LogCapturer:
            def write(self, txt):
                if txt.strip():
                    active_tasks[task_id]['logs'].append(txt.strip())
            def flush(self):
                pass
        
        old_stdout = sys.stdout
        sys.stdout = LogCapturer()
        
        try:
            # Parse duration(s)
            dur_val = params.get('duration', 7)
            if isinstance(dur_val, str) and ',' in dur_val:
                duration = [int(d.strip()) for d in dur_val.split(',')]
            elif isinstance(dur_val, str):
                try:
                    duration = int(dur_val)
                except ValueError:
                    duration = 7
            else:
                duration = dur_val

            cabin_class = params.get('cabin_class', 'ECONOMY')
            stops_limit = params.get('stops_limit', 'ANY')
            adults = int(params.get('adults', 1))

            if task_type == 'search':
                nearby = params.get('nearby', False)
                if nearby:
                    start_date, end_date = agent.parse_date_range(params['dates'])
                    results = agent.search_with_nearby(
                        origin=params['origin'],
                        destination=params['destination'],
                        date_start=start_date,
                        date_end=end_date,
                        trip_duration=duration,
                        cabin_class=cabin_class,
                        stops_limit=stops_limit,
                        adults=adults
                    )
                else:
                    results = agent.search(
                        origin=params['origin'],
                        destination=params['destination'],
                        date_range=params['dates'],
                        trip_duration=duration,
                        cabin_class=cabin_class,
                        stops_limit=stops_limit,
                        adults=adults
                    )
            elif task_type == 'explore':
                results = agent.explore(
                    origin=params['origin'],
                    date_range=params['dates'],
                    trip_duration=duration,
                    regions=params.get('regions'),
                    budget=params.get('budget')
                )
            elif task_type == 'dates':
                durations = params.get('durations', [7])
                if isinstance(durations, str):
                    durations = [int(d) for d in durations.split(',')]
                results = agent.date_grid(
                    origin=params['origin'],
                    destination=params['destination'],
                    date_range=params['dates'],
                    trip_durations=durations
                )
            elif task_type == 'flexible':
                start_date, end_date = agent.parse_date_range(params['dates'])
                min_days = int(params.get('min_days', 5))
                max_days = int(params.get('max_days', 10))
                budget = params.get('budget')
                if budget:
                    budget = float(budget)
                results = agent.flexible_search(
                    origin=params['origin'],
                    destination=params['destination'],
                    date_start=start_date,
                    date_end=end_date,
                    min_days=min_days,
                    max_days=max_days,
                    budget=budget,
                    cabin_class=cabin_class,
                    stops_limit=stops_limit,
                    adults=adults
                )
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
            active_tasks[task_id]['status'] = 'completed'
            active_tasks[task_id]['results'] = results
            active_tasks[task_id]['logs'].append("Search completed successfully!")
        finally:
            sys.stdout = old_stdout
            
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        active_tasks[task_id]['status'] = 'failed'
        active_tasks[task_id]['error'] = str(e)
        active_tasks[task_id]['logs'].append(f"Error occurred: {e}")
        active_tasks[task_id]['logs'].append(f"Traceback:\n{tb}")

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/routes', methods=['GET'])
def get_routes():
    db = FlightDB()
    try:
        cursor = db.conn.cursor()
        cursor.execute('''
            SELECT origin, destination, COUNT(*), MIN(price), MAX(price), AVG(price)
            FROM price_history 
            GROUP BY origin, destination
            ORDER BY MIN(price) ASC
        ''')
        rows = cursor.fetchall()
        routes = []
        for r in rows:
            routes.append({
                'origin': r[0],
                'destination': r[1],
                'count': r[2],
                'min_price': r[3] if r[3] is not None else 0,
                'max_price': r[4] if r[4] is not None else 0,
                'avg_price': round(r[5], 2) if r[5] is not None else 0
            })
        return jsonify(routes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/history', methods=['GET'])
def get_history():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    
    db = FlightDB()
    try:
        cursor = db.conn.cursor()
        if origin and destination:
            cursor.execute('''
                SELECT departure_date, return_date, price, airline, stops, duration_minutes, checked_at, via
                FROM price_history
                WHERE origin=? AND destination=?
                ORDER BY checked_at DESC, price ASC
            ''', (origin.upper(), destination.upper()))
            rows = cursor.fetchall()
            flights = []
            for r in rows:
                flights.append({
                    'departure_date': r[0],
                    'return_date': r[1],
                    'price': r[2],
                    'airline': r[3],
                    'stops': r[4],
                    'duration_minutes': r[5],
                    'checked_at': r[6],
                    'via': r[7]
                })
            return jsonify(flights)
        else:
            return jsonify({'error': 'Origin and destination parameters are required'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/search', methods=['POST'])
def start_search():
    data = request.json or {}
    task_type = data.get('type', 'search')
    
    if task_type == 'explore':
        if not data.get('origin') or not data.get('dates'):
            return jsonify({'error': 'Missing required fields: origin, dates'}), 400
    else:
        if not data.get('origin') or not data.get('destination') or not data.get('dates'):
            return jsonify({'error': 'Missing required fields: origin, destination, dates'}), 400
            
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = {
        'status': 'pending',
        'logs': [],
        'results': [],
        'timestamp': datetime.now().isoformat()
    }
    
    thread = threading.Thread(target=run_agent_search, args=(task_id, task_type, data))
    thread.daemon = True
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'pending'})

@app.route('/api/search/status/<task_id>', methods=['GET'])
def search_status(task_id):
    task = active_tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)

@app.route('/api/alerts', methods=['GET', 'POST'])
def handle_alerts():
    db = FlightDB()
    try:
        if request.method == 'GET':
            cursor = db.conn.cursor()
            cursor.execute('SELECT * FROM alerts ORDER BY created_at DESC')
            rows = cursor.fetchall()
            alerts = []
            for r in rows:
                alerts.append({
                    'id': r[0],
                    'origin': r[1],
                    'destination': r[2],
                    'departure_date_start': r[3],
                    'departure_date_end': r[4],
                    'trip_duration_days': r[5],
                    'target_price': r[6],
                    'currency': r[7],
                    'is_active': bool(r[8]),
                    'created_at': r[9],
                    'triggered_at': r[10],
                    'best_price_found': r[11],
                    'best_date_found': r[12]
                })
            return jsonify(alerts)
            
        elif request.method == 'POST':
            data = request.json or {}
            origin = data.get('origin', '').upper()
            destination = data.get('destination', '').upper()
            date_start = data.get('departure_date_start')
            date_end = data.get('departure_date_end')
            trip_duration = int(data.get('trip_duration_days', 7))
            target_price = float(data.get('target_price', 10000))
            
            if not origin or not destination or not date_start or not date_end:
                return jsonify({'error': 'Missing required fields'}), 400
                
            alert_id = db.create_alert(origin, destination, date_start, date_end, trip_duration, target_price)
            return jsonify({'message': 'Alert created successfully', 'alert_id': alert_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    db = FlightDB()
    try:
        cursor = db.conn.cursor()
        cursor.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
        db.conn.commit()
        return jsonify({'message': 'Alert deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/alerts/check', methods=['POST'])
def trigger_alert_check():
    def run_check():
        agent = FlightAgent()
        try:
            agent.check_alerts()
        except Exception as e:
            print(f"Alert check failed: {e}")
            
    thread = threading.Thread(target=run_check)
    thread.daemon = True
    thread.start()
    return jsonify({'message': 'Alert scan triggered in the background'})

if __name__ == '__main__':
    # Default Flask configuration
    app.run(host='127.0.0.1', port=5000, debug=True)
