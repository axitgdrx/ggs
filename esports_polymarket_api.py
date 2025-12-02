import requests
import json
import math
from typing import List, Dict
from polymarket_api import PolymarketAPI
from team_mapping import normalize_team_name

class EsportsPolymarketAPI(PolymarketAPI):
    # Tags: LoL, Dota 2, CS2, Valorant
    TAGS = ["65", "102366", "100780", "101672"]

    def get_esports_games(self) -> List[Dict]:
        """
        Get Esports games from Polymarket
        """
        all_games = []
        
        # We fetch events for each tag
        # To avoid duplicates if an event has multiple tags, we track IDs
        seen_ids = set()

        for tag_id in self.TAGS:
            events = self.get_events_by_tag(tag_id, limit=100)
            
            for event in events:
                if event['id'] in seen_ids:
                    continue
                seen_ids.add(event['id'])

                title = event.get('title', '')
                slug = event.get('slug', '')

                # Filter for game events (must contain ' vs ' or ' vs. ')
                if ' vs ' not in title and ' vs. ' not in title:
                    continue

                # Extract team names
                separator = ' vs. ' if ' vs. ' in title else ' vs '
                teams = title.split(separator)
                if len(teams) != 2:
                    continue

                away_team = teams[0].strip()
                home_team = teams[1].strip()

                # Get team codes - for esports we use name as fallback code
                # We can try to normalize but often names are just names
                away_code = normalize_team_name(away_team, 'polymarket') or away_team
                home_code = normalize_team_name(home_team, 'polymarket') or home_team

                # Find the Game Winner market
                winner_market = None
                for market in event.get('markets', []):
                    question = market.get('question', '')
                    # Exact match
                    if question == title:
                        winner_market = market
                        break
                    # Or "Match Winner" / "Moneyline"
                    if 'Winner' in question or 'Moneyline' in question:
                         # Avoid "Map 1 Winner", "Map 2 Winner" unless the title implies it
                         if 'Map' not in question and '1H' not in question:
                             winner_market = market
                             break
                
                if not winner_market:
                    continue

                # Parse outcomes and prices
                try:
                    outcomes = json.loads(winner_market.get('outcomes', '[]'))
                    prices = json.loads(winner_market.get('outcomePrices', '[]'))

                    if len(outcomes) != 2 or len(prices) != 2:
                        continue

                    # Process outcomes
                    outcome_data = []
                    for outcome, price in zip(outcomes, prices):
                        # Use outcome name as code fallback
                        code = normalize_team_name(outcome, 'polymarket') or outcome
                        outcome_data.append({
                            'code': code,
                            'raw_prob': float(price) * 100,
                            'name': outcome
                        })

                    if len(outcome_data) != 2:
                        continue

                    # Normalize probabilities
                    prob1 = outcome_data[0]['raw_prob']
                    prob2 = outcome_data[1]['raw_prob']

                    floor1 = math.floor(prob1)
                    floor2 = math.floor(prob2)
                    remainder = 100 - (floor1 + floor2)

                    if prob1 <= prob2:
                        outcome_data[0]['prob'] = floor1 + remainder
                        outcome_data[1]['prob'] = floor2
                    else:
                        outcome_data[0]['prob'] = floor1
                        outcome_data[1]['prob'] = floor2 + remainder

                    # Map to team codes (or names if code is same as name)
                    # We need to match away/home from title to outcomes
                    # Usually order in title matches order in outcomes? Not always.
                    
                    # Try to match names
                    probs = {}
                    
                    # Helper to check if string a contains b roughly
                    def is_match(a, b):
                        return a.lower() in b.lower() or b.lower() in a.lower()

                    # Assign probs based on name matching
                    # This is tricky for esports. 
                    # If we can't match, we assume order? 
                    # Usually "Away vs Home".
                    
                    # Let's try to match outcome name to title teams
                    mapped_probs = {}
                    for item in outcome_data:
                        if is_match(item['name'], away_team):
                            mapped_probs['away'] = item['prob']
                            mapped_probs['away_raw'] = item['raw_prob']
                        elif is_match(item['name'], home_team):
                            mapped_probs['home'] = item['prob']
                            mapped_probs['home_raw'] = item['raw_prob']
                            
                    if 'away' in mapped_probs and 'home' in mapped_probs:
                        away_prob = mapped_probs['away']
                        home_prob = mapped_probs['home']
                        away_raw = mapped_probs['away_raw']
                        home_raw = mapped_probs['home_raw']
                    else:
                        # Fallback: assume order matches? Or skip?
                        # Often outcomes are [Team A, Team B].
                        # Let's rely on checking if outcome matches one of the teams
                        continue

                    game_data = {
                        'platform': 'Polymarket',
                        'market_id': winner_market.get('id'),
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_code': away_code,
                        'home_code': home_code,
                        'away_prob': away_prob,
                        'home_prob': home_prob,
                        'away_raw_price': away_raw,
                        'home_raw_price': home_raw,
                        'slug': slug,
                        'end_date': winner_market.get('endDate', ''),
                        'url': f'https://polymarket.com/event/{slug}',
                        'sport': 'ESPORTS'
                    }

                    all_games.append(game_data)

                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Error parsing market data for {title}: {e}")
                    continue

        return all_games
