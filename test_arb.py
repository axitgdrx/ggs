#!/usr/bin/env python3
from api import fetch_all_sports_data
from paper_trading import PaperTradingSystem

# Fetch data
print("Fetching data...")
data = fetch_all_sports_data(force_refresh=True)
print(f'Found {len(data.get("matched_games", []))} matched games')

# Test arbitrage on each game
trader = PaperTradingSystem()
arb_count = 0
for match in data.get('matched_games', []):
    poly = match['polymarket']
    kalshi = match['kalshi']
    
    game = {
        'away_team': poly['away_team'],
        'home_team': poly['home_team'],
        'away_code': poly['away_code'],
        'home_code': poly['home_code'],
        'sport': poly.get('sport', 'unknown'),
        'polymarket': {
            'away': poly['away_prob'],
            'home': poly['home_prob'],
            'raw_away': poly['away_raw_price'],
            'raw_home': poly['home_raw_price'],
            'market_id': poly['market_id'],
            'url': poly['url']
        },
        'kalshi': {
            'away': kalshi['away_prob'],
            'home': kalshi['home_prob'],
            'raw_away': kalshi['away_raw_price'],
            'raw_home': kalshi['home_raw_price'],
            'away_ticker': kalshi.get('ticker'),
            'home_ticker': kalshi.get('ticker'),
            'url': kalshi['url']
        }
    }
    
    success, result = trader.execute_arb(game)
    if success:
        arb_count += 1
        print(f'✅ ARB: {game["away_team"]} vs {game["home_team"]} - Profit: ${result["profit"]:.2f} ({result["roi_percent"]:.2f}%)')
    else:
        if arb_count < 5:  # Show first few failures
            print(f'❌ No arb: {game["away_team"]} vs {game["home_team"]} - {result}')

print(f'\nTotal arbitrage opportunities: {arb_count}')