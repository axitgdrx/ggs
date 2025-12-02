import requests
import math
from typing import List, Dict
from collections import defaultdict
from kalshi_api import KalshiAPI
from team_mapping import normalize_team_name

class EsportsKalshiAPI(KalshiAPI):
    TICKERS = [
        "KXCS2", "KXDOTA2", "KXOVERWATCH", "KXCSGO", 
        "KXESPORTS", "KXLOL", "KXDOTA", "KXVALORANT"
    ]

    def get_esports_games(self) -> List[Dict]:
        """
        Get Esports games from Kalshi (Head-to-Head only for now)
        """
        all_games = []
        
        # Avoid processing same market twice
        seen_ids = set()

        for series_ticker in self.TICKERS:
            markets = self.get_markets_by_ticker(series_ticker, limit=100)
            
            # Group by game
            games_dict = defaultdict(dict)

            for market in markets:
                ticker = market.get('ticker', '')
                if ticker in seen_ids:
                    continue
                seen_ids.add(ticker)
                
                title = market.get('title', '')
                
                # Looking for H2H: "Team A vs Team B Winner?"
                if ' vs ' not in title or 'Winner?' not in title:
                    # Skip futures/tournaments for now
                    continue

                parts = ticker.split('-')
                if len(parts) < 3:
                    continue

                # Ticker format usually: KXSERIES-DATE-GAME-TEAM
                # But for esports it might vary.
                # Let's rely on title parsing mainly.
                
                title_clean = title.replace(' Winner?', '')
                teams = title_clean.split(' vs ')
                if len(teams) != 2:
                    continue

                away_team = teams[0].strip()
                home_team = teams[1].strip()
                
                # Use name as code fallback
                away_code = normalize_team_name(away_team, 'kalshi') or away_team
                home_code = normalize_team_name(home_team, 'kalshi') or home_team

                # Identify which team this market is for
                # Kalshi tickers end with the team code usually, but for esports 
                # the "code" might be ad-hoc.
                # Let's check the result outcome in market? Kalshi API doesn't always give "outcome" name in list.
                # But 'subtitle' or 'title' helps.
                
                # However, the market title is usually "Team A vs Team B Winner?".
                # But how do we know if this market is for Team A or Team B?
                # Usually there are 2 markets.
                # One has subtitle "Team A", other "Team B".
                
                subtitle = market.get('subtitle', '')
                target_team = None
                
                if subtitle == away_team:
                    target_team = 'away'
                elif subtitle == home_team:
                    target_team = 'home'
                else:
                    # Try fuzzy match
                    if away_team in subtitle:
                        target_team = 'away'
                    elif home_team in subtitle:
                        target_team = 'home'
                
                if not target_team:
                    continue

                # Construct a game_id from teams to group them
                # Sort teams to ensure consistency
                # But we need to distinguish away/home. 
                # Let's use the ticker prefix excluding the last part
                game_id = "-".join(parts[:-1])
                
                if game_id not in games_dict:
                     games_dict[game_id] = {
                        'platform': 'Kalshi',
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_code': away_code,
                        'home_code': home_code,
                        'close_time': market.get('close_time', ''),
                        'ticker': ticker, # This will be overwritten but that's ok
                        'sport': 'ESPORTS'
                    }
                
                prob = market.get('last_price', 0)
                
                if target_team == 'away':
                    games_dict[game_id]['away_prob'] = prob
                    games_dict[game_id]['away_ticker'] = ticker
                else:
                    games_dict[game_id]['home_prob'] = prob
                    games_dict[game_id]['home_ticker'] = ticker

            # Convert to list
            for gid, g in games_dict.items():
                if 'away_prob' in g and 'home_prob' in g:
                     # Normalize
                    away_raw = g['away_prob']
                    home_raw = g['home_prob']
                    total = away_raw + home_raw
                    
                    if total > 0:
                        away_pct = (away_raw / total) * 100
                        home_pct = (home_raw / total) * 100
                        
                        away_floor = math.floor(away_pct)
                        home_floor = math.floor(home_pct)
                        remainder = 100 - (away_floor + home_floor)
                        
                        if away_raw <= home_raw:
                            g['away_prob'] = away_floor + remainder
                            g['home_prob'] = home_floor
                        else:
                            g['away_prob'] = away_floor
                            g['home_prob'] = home_floor + remainder
                    else:
                        g['away_prob'] = 0
                        g['home_prob'] = 0
                    
                    g['away_raw_price'] = away_raw
                    g['home_raw_price'] = home_raw
                        
                    # Url
                    if 'away_ticker' in g:
                         g['url'] = f"https://kalshi.com/markets/{g['away_ticker']}"
                         
                    all_games.append(g)
                    
        return all_games
