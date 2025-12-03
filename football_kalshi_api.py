#!/usr/bin/env python3
"""Kalshi API for Football/Soccer games"""

import requests
import math
from typing import List, Dict
from collections import defaultdict
from kalshi_api import KalshiAPI
from football_team_mapping import normalize_team_name


class FootballKalshiAPI(KalshiAPI):
    FOOTBALL_SERIES = ["KXSOCCER", "KXEPLGAME", "KXUCLGAME", "KXUELGAME", "KXSOCCERGAME"]

    def __init__(self):
        super().__init__()

    def get_football_games(self) -> List[Dict]:
        """Get football games from Kalshi"""
        football_markets = []
        
        # Fetch markets for each series
        for series in self.FOOTBALL_SERIES:
            markets = self.get_markets_by_ticker(series, limit=100)
            football_markets.extend(markets)
        
        return self._process_markets(football_markets)

    def _process_markets(self, markets: List[Dict]) -> List[Dict]:
        try:
            games_dict = defaultdict(dict)

            for market in markets:
                title = market.get('title', '')
                if 'win' not in title.lower():
                    continue

                ticker = market.get('ticker', '')
                parts = ticker.split('-')
                if len(parts) < 3:
                    continue

                game_id = parts[1]
                team_code = parts[2] if len(parts) > 2 else ''

                title_clean = title.replace(' Winner?', '').replace(' winner?', '').replace(' Win?', '').replace(' win?', '')
                if ' vs ' in title_clean:
                    teams = title_clean.split(' vs ')
                elif ' at ' in title_clean:
                    teams = title_clean.split(' at ')
                elif ' v ' in title_clean:
                    teams = title_clean.split(' v ')
                else:
                    continue

                if len(teams) != 2:
                    continue

                away_team = teams[0].strip()
                home_team = teams[1].strip()

                away_code = normalize_team_name(away_team, 'kalshi')
                home_code = normalize_team_name(home_team, 'kalshi')

                if not away_code or not home_code:
                    continue

                last_price = market.get('last_price', 0)
                yes_bid = market.get('yes_bid', 0)
                yes_ask = market.get('yes_ask', 0)

                # Prioritize bid/ask midpoint for better accuracy
                if yes_bid > 0 and yes_ask > 0:
                    probability = (yes_bid + yes_ask) / 2
                elif last_price > 0:
                    probability = last_price
                elif yes_ask > 0:
                    probability = yes_ask
                elif yes_bid > 0:
                    probability = yes_bid
                else:
                    probability = 0

                if game_id not in games_dict:
                    games_dict[game_id] = {
                        'platform': 'Kalshi',
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_code': away_code,
                        'home_code': home_code,
                        'close_time': market.get('close_time', ''),
                        'ticker': ticker,
                    }

                if team_code == 'TIE':
                    continue

                if team_code == away_code or normalize_team_name(team_code, 'kalshi') == away_code:
                    games_dict[game_id]['away_raw'] = probability
                elif team_code == home_code or normalize_team_name(team_code, 'kalshi') == home_code:
                    games_dict[game_id]['home_raw'] = probability

            games = []
            for game_id, game_data in games_dict.items():
                if 'away_raw' in game_data and 'home_raw' in game_data:
                    away_raw = game_data['away_raw']
                    home_raw = game_data['home_raw']
                    total = away_raw + home_raw

                    if total > 0:
                        away_pct = (away_raw / total) * 100
                        home_pct = (home_raw / total) * 100

                        away_floor = math.floor(away_pct)
                        home_floor = math.floor(home_pct)
                        remainder = 100 - (away_floor + home_floor)

                        if away_raw <= home_raw:
                            away_prob = away_floor + remainder
                            home_prob = home_floor
                        else:
                            away_prob = away_floor
                            home_prob = home_floor + remainder
                    else:
                        away_prob = 0
                        home_prob = 0

                    game_data['away_prob'] = away_prob
                    game_data['home_prob'] = home_prob

                    ticker = game_data.get('ticker', '')
                    if ticker:
                        game_data['url'] = f'https://kalshi.com/markets/{ticker}'

                    games.append(game_data)

            return games

        except Exception as e:
            print(f"Error processing football data from Kalshi: {e}")
            return []


if __name__ == '__main__':
    api = FootballKalshiAPI()
    games = api.get_football_games()
    print(f"\nFound {len(games)} football games on Kalshi:")
    for game in games[:5]:
        print(f"  {game['away_team']} @ {game['home_team']}: {game['away_prob']}% vs {game['home_prob']}%")
