# ✈️ Flight Price Checker Agent

Professional flight search tool implementing 5 Google Flights pro strategies.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get SerpAPI key from [https://serpapi.com](https://serpapi.com) (free tier: 100 searches/month)

# 3. Add your key to .env
SERPAPI_KEY=your_key_here

# 4. Run searches
python main.py explore --from LKO --dates "2024-08"
python main.py search --from LKO --to DXB --dates "2024-08"
python main.py dates --from LKO --to BKK --dates "2024-08" --durations 5 7
python main.py alert --from LKO --to SIN --dates "2024-08" --target 20000
python main.py monitor
```
