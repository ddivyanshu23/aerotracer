import sys, io, sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect('flights.db')
c = conn.cursor()

print('=' * 80)
print('  FLIGHT PRICE CHECKER AGENT - DATABASE REPORT')
print('=' * 80)

# Route summary
c.execute('''SELECT origin, destination, COUNT(*), MIN(price), MAX(price), AVG(price)
             FROM price_history GROUP BY origin, destination''')
routes = c.fetchall()
print(f'\n  Routes tracked: {len(routes)}\n')
for r in routes:
    symbol = '\u20b9'
    print(f'  {r[0]} -> {r[1]}')
    print(f'    Records: {r[2]}  |  Cheapest: {symbol}{r[3]:,.0f}  |  Most Expensive: {symbol}{r[4]:,.0f}  |  Average: {symbol}{r[5]:,.0f}')
    print()

# Top 10 cheapest unique flights per route
for route in routes:
    origin, dest = route[0], route[1]
    print(f'\n  Top 10 cheapest: {origin} -> {dest}')
    print(f'  {"-" * 70}')
    c.execute('''SELECT departure_date, return_date, price, airline, stops, duration_minutes
                 FROM price_history 
                 WHERE origin=? AND destination=?
                 GROUP BY departure_date, return_date, price, airline
                 ORDER BY price ASC LIMIT 10''', (origin, dest))
    rows = c.fetchall()
    for i, row in enumerate(rows, 1):
        dep, ret, price, airline, stops, dur = row
        hrs = dur // 60
        mins = dur % 60
        print(f'    {i:>2}. {dep} to {ret}  |  \u20b9{price:,.0f}  |  {airline}  |  {stops} stop(s)  |  {hrs}h {mins}m')

conn.close()
print(f'\n{"=" * 80}')
