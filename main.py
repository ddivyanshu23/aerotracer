'''
Flight Price Checker Agent - CLI Entry Point

Usage:
    python main.py explore --from LKO --dates "2026-08" --duration 7
    python main.py search --from LKO --to DXB --dates "2026-08" --duration 5
    python main.py dates --from LKO --to NRT --dates "2026-09" --durations 7 10
    python main.py alert --from LKO --to BKK --dates "2026-08" --target 18000
    python main.py full --from LKO --to LHR --dates "2026-09" --duration 10
    python main.py history                          # show all saved routes
    python main.py history --from LKO --to GOI      # show cheapest for a route
    python main.py monitor
'''

import argparse
import schedule
import time
import sys
import io

if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from flight_agent import FlightAgent
from database import FlightDB
from config import Config


def show_history(origin=None, destination=None, top_n=20):
    """Show saved flight data from the database."""
    db = FlightDB()
    cursor = db.conn.cursor()
    symbol = "₹" if Config.CURRENCY == "INR" else "$"

    if origin and destination:
        origin = origin.upper()
        destination = destination.upper()

        # Show cheapest flights for a specific route
        cursor.execute('''
            SELECT departure_date, return_date, price, airline, stops, duration_minutes, checked_at
            FROM price_history
            WHERE origin=? AND destination=?
            GROUP BY departure_date, return_date, price, airline
            ORDER BY price ASC LIMIT ?
        ''', (origin, destination, top_n))
        rows = cursor.fetchall()

        if not rows:
            print(f"\n   ⚠️  No saved flights for {origin} → {destination}")
            db.close()
            return

        # Route stats
        cursor.execute('''
            SELECT COUNT(*), MIN(price), MAX(price), AVG(price)
            FROM price_history WHERE origin=? AND destination=?
        ''', (origin, destination))
        stats = cursor.fetchone()

        print(f'''
╔══════════════════════════════════════════════════════════════╗
║  📊 PRICE HISTORY: {origin} → {destination:<10}                        ║
╠══════════════════════════════════════════════════════════════╣
║  Total Records: {stats[0]:<5}                                        ║
║  Cheapest:  {symbol}{stats[1]:>10,.0f}                                    ║
║  Expensive: {symbol}{stats[2]:>10,.0f}                                    ║
║  Average:   {symbol}{stats[3]:>10,.0f}                                    ║
╚══════════════════════════════════════════════════════════════╝
        ''')

        print(f"  Top {min(top_n, len(rows))} cheapest flights:\n")
        for i, row in enumerate(rows, 1):
            dep, ret, price, airline, stops, dur, checked = row
            hrs = dur // 60
            mins = dur % 60
            trip_type = f"{dep} → {ret}" if ret else dep
            print(f"  {i:>3}. {symbol}{price:>10,.0f}  |  {trip_type}  |  {airline}")
            print(f"       {stops} stop(s)  |  {hrs}h {mins}m  |  saved: {checked}")
            print()

    else:
        # Show summary of all routes
        cursor.execute('''
            SELECT origin, destination, COUNT(*), MIN(price), MAX(price), AVG(price)
            FROM price_history GROUP BY origin, destination
            ORDER BY MIN(price) ASC
        ''')
        routes = cursor.fetchall()

        if not routes:
            print("\n   ⚠️  No flight data saved yet. Run a search first!")
            db.close()
            return

        print(f'''
╔══════════════════════════════════════════════════════════════╗
║  📊 ALL SAVED ROUTES                                        ║
╚══════════════════════════════════════════════════════════════╝
        ''')

        for r in routes:
            origin_r, dest_r, count, min_p, max_p, avg_p = r
            print(f"  ✈️  {origin_r} → {dest_r}")
            print(f"      {count} records  |  Cheapest: {symbol}{min_p:,.0f}  |  Avg: {symbol}{avg_p:,.0f}  |  Max: {symbol}{max_p:,.0f}")
            print()

        print(f"  💡 Tip: Run  python main.py history --from DEL --to BOM  for details\n")

    db.close()


def parse_durations(val):
    if ',' in val:
        return [int(x.strip()) for x in val.split(',')]
    try:
        return int(val)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid duration value: '{val}'. Must be int or comma-separated list of ints.")


def main():
    parser = argparse.ArgumentParser(description="✈️ Flight Price Checker Agent")
    subparsers = parser.add_subparsers(dest="command")

    # EXPLORE
    exp = subparsers.add_parser("explore", help="Find cheapest destinations")
    exp.add_argument("--from", dest="origin", required=True)
    exp.add_argument("--dates", required=True)
    exp.add_argument("--duration", type=parse_durations, default=7)
    exp.add_argument("--regions", nargs="+")
    exp.add_argument("--budget", type=int)

    # SEARCH
    src = subparsers.add_parser("search", help="Smart filtered search")
    src.add_argument("--from", dest="origin", required=True)
    src.add_argument("--to", dest="destination", required=True)
    src.add_argument("--dates", required=True)
    src.add_argument("--duration", type=parse_durations, default=7)

    # DATE GRID
    dg = subparsers.add_parser("dates", help="Date grid scanner")
    dg.add_argument("--from", dest="origin", required=True)
    dg.add_argument("--to", dest="destination", required=True)
    dg.add_argument("--dates", required=True)
    dg.add_argument("--durations", nargs="+", type=int, default=[7])

    # ALERT
    al = subparsers.add_parser("alert", help="Set price alert")
    al.add_argument("--from", dest="origin", required=True)
    al.add_argument("--to", dest="destination", required=True)
    al.add_argument("--dates", required=True)
    al.add_argument("--duration", type=parse_durations, default=7)
    al.add_argument("--target", type=int)

    # FULL
    fa = subparsers.add_parser("full", help="Full analysis")
    fa.add_argument("--from", dest="origin", required=True)
    fa.add_argument("--to", dest="destination", required=True)
    fa.add_argument("--dates", required=True)
    fa.add_argument("--duration", type=parse_durations, default=7)

    # HISTORY (NEW)
    hi = subparsers.add_parser("history", help="View saved flight data from database")
    hi.add_argument("--from", dest="origin", default=None)
    hi.add_argument("--to", dest="destination", default=None)
    hi.add_argument("--top", type=int, default=20, help="Number of results to show")

    # MONITOR
    subparsers.add_parser("monitor", help="Run continuous monitoring")

    args = parser.parse_args()

    if args.command == "history":
        show_history(args.origin, args.destination, args.top)
    elif args.command in ("explore", "search", "dates", "alert", "full", "monitor"):
        agent = FlightAgent()

        if args.command == "explore":
            agent.explore(args.origin, args.dates, args.duration, args.regions, args.budget)
        elif args.command == "search":
            agent.search(args.origin, args.destination, args.dates, args.duration)
        elif args.command == "dates":
            agent.date_grid(args.origin, args.destination, args.dates, args.durations)
        elif args.command == "alert":
            agent.set_alert(args.origin, args.destination, args.dates, args.duration, args.target)
        elif args.command == "full":
            agent.full_analysis(args.origin, args.destination, args.dates, args.duration)
        elif args.command == "monitor":
            print(f"\n🔄 Monitoring every {Config.CHECK_INTERVAL_MINUTES} min...\n")
            agent.check_alerts()
            schedule.every(Config.CHECK_INTERVAL_MINUTES).minutes.do(agent.check_alerts)
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(30)
            except KeyboardInterrupt:
                print("\n⏹️ Stopped.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
