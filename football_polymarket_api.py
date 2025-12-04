#!/usr/bin/env python3
"""Polymarket API for Football/Soccer games"""

import json
import math
import re
from typing import Dict, List, Optional

import requests

from polymarket_api import PolymarketAPI
from football_team_mapping import normalize_team_name


class FootballPolymarketAPI(PolymarketAPI):
    FOOTBALL_LEAGUES = [
        "epl",  # English Premier League
        "lal",  # La Liga
        "bun",  # Bundesliga
        "ser",  # Serie A
        "lig",  # Ligue 1
        "ucl",  # Champions League
        "uel",  # Europa League
        "col",  # Conference League
    ]

    def __init__(self):
        super().__init__()
        # tag_ids fetching logic removed/deprecated as we fetch all events and filter

    def get_football_games(self) -> List[Dict]:
        """Fetch every open football game from Polymarket."""
        # Specific league tags to ensure we get relevant games
        # 82: EPL, 780: La Liga, 1494: Bundesliga, 1234: UCL, 101787: UEL
        league_tags = ["82", "780", "1494", "1234", "101787"]
        
        events = {}
        for tag_id in league_tags:
            tag_events = self.get_events_by_tag(tag_id, limit=200)
            for event in tag_events:
                # Deduplicate by slug
                slug = event.get("slug") or event.get("id") or event.get("title")
                if slug and slug not in events:
                    events[slug] = event

        games = []
        for event in events.values():
            if not self._is_football_event(event):
                # Trust tag, but double check
                pass

            game = self._parse_game(event)
            if game:
                games.append(game)

        return games

    def _is_football_event(self, event: Dict) -> bool:
        """Ensure the event is a football match."""
        tags = event.get("tags") or []
        for tag in tags:
            label = (tag.get("label") or "").lower()
            slug = (tag.get("slug") or "").lower()
            if any(keyword in label for keyword in ("soccer", "football", "premier league", "la liga", "bundesliga", "champions")):
                return True
            if any(keyword in slug for keyword in ("soccer", "football", "epl", "ucl")):
                return True

        title = (event.get("title") or "").lower()
        return any(kw in title for kw in ("vs", "vs.", "@", " at "))

    def _normalize_pair(self, prob1, prob2):
        """Normalize two probabilities to sum to 100."""
        total = prob1 + prob2
        if total <= 0:
            return 0, 0
            
        new_p1 = (prob1 / total) * 100
        new_p2 = (prob2 / total) * 100
        
        f1 = math.floor(new_p1)
        f2 = math.floor(new_p2)
        rem = 100 - (f1 + f2)
        
        # Add remainder to the larger one
        if f1 >= f2:
            f1 += rem
        else:
            f2 += rem
            
        return f1, f2

    def _parse_game(self, event: Dict):
        try:
            raw_title = event.get("title", "")
            if not raw_title:
                return None

            matchup_title = self._strip_league_prefix(raw_title)
            teams = self._split_matchup(matchup_title)
            if not teams:
                return None

            away_team = self._clean_team_name(teams[0])
            home_team = self._clean_team_name(teams[1])

            away_code = normalize_team_name(away_team, "polymarket")
            home_code = normalize_team_name(home_team, "polymarket")
            
            if not away_code or not home_code:
                # Try to clean name further if initial mapping failed
                # e.g. "Liverpool FC" -> "Liverpool" is handled by _clean_team_name or normalize_team_name
                return None

            winner_market = self._find_winner_market(event.get("markets", []), raw_title)
            
            # Check if we should use binary parsing (if no single winner market, or if it's a binary one)
            if not winner_market or self._is_binary_market(winner_market):
                return self._parse_binary_game(event, away_team, home_team, away_code, home_code)

            outcome_data = self._parse_outcomes(winner_market, away_team, home_team)
            if len(outcome_data) < 2:
                # If outcome parsing failed, maybe it is a binary market disguised as winner market?
                return self._parse_binary_game(event, away_team, home_team, away_code, home_code)

            probs = self._normalize_probabilities(outcome_data, away_code, home_code)
            slug = event.get("slug", "")

            return {
                "away_team": away_team,
                "home_team": home_team,
                "away_code": away_code,
                "home_code": home_code,
                "away_prob": probs.get(away_code, 0),
                "home_prob": probs.get(home_code, 0),
                "market_id": winner_market.get("id") if winner_market else None,
                "end_date": event.get("endDate", ""),
                "slug": slug,
                "url": f"https://polymarket.com/event/{slug}" if slug else "",
            }

        except Exception as e:
            # print(f"Error parsing game {event.get('title')}: {e}")
            return None

    def _is_binary_market(self, market: Dict) -> bool:
        """Check if market has Yes/No outcomes."""
        if not market:
            return False
        outcomes_raw = market.get("outcomes", "[]")
        outcomes = json.loads(outcomes_raw) if isinstance(outcomes_raw, str) else outcomes_raw
        if len(outcomes) == 2 and "Yes" in outcomes and "No" in outcomes:
            return True
        return False

    def _parse_binary_game(self, event: Dict, away_team: str, home_team: str, away_code: str, home_code: str):
        """Parse game with separate binary markets for each team."""
        markets = event.get("markets", [])
        
        away_prob = 0
        home_prob = 0
        
        found_away = False
        found_home = False
        
        away_market_id = None
        home_market_id = None
        
        for market in markets:
            question = market.get("question", "")
            
            # Check for Away Team Win
            if away_team in question and "win" in question.lower() and "draw" not in question.lower():
                prob = self._get_binary_yes_price(market)
                if prob is not None:
                    away_prob = prob
                    found_away = True
                    away_market_id = market.get("id")
            
            # Check for Home Team Win
            elif home_team in question and "win" in question.lower() and "draw" not in question.lower():
                prob = self._get_binary_yes_price(market)
                if prob is not None:
                    home_prob = prob
                    found_home = True
                    home_market_id = market.get("id")
        
        # If we didn't match by exact name, try matching by code/mapping names
        if not found_away:
             # Try to find market with mapping names
             info = normalize_team_name(away_team, 'polymarket') # this returns code
             pass

        if found_away or found_home:
            # Do not normalize for Soccer
            # norm_away, norm_home = self._normalize_pair(away_prob, home_prob)
            
            slug = event.get("slug", "")
            return {
                "away_team": away_team,
                "home_team": home_team,
                "away_code": away_code,
                "home_code": home_code,
                "away_prob": away_prob,
                "home_prob": home_prob,
                "away_market_id": away_market_id,
                "home_market_id": home_market_id,
                "end_date": event.get("endDate", ""),
                "slug": slug,
                "url": f"https://polymarket.com/event/{slug}" if slug else "",
            }
            
        return None

    def _get_binary_yes_price(self, market: Dict) -> Optional[float]:
        outcomes_raw = market.get("outcomes", "[]")
        prices_raw = market.get("outcomePrices", "[]")
        
        outcomes = json.loads(outcomes_raw) if isinstance(outcomes_raw, str) else outcomes_raw
        prices = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
        
        if "Yes" in outcomes:
            idx = outcomes.index("Yes")
            if idx < len(prices):
                return float(prices[idx])
        return None

    def _strip_league_prefix(self, title: str) -> str:
        """Remove leading league identifiers."""
        prefix_pattern = re.compile(r"^\s*(epl|ucl|uel|premier league|champions league|la liga|bundesliga|serie a|ligue 1)\s*[:\-]\s*", re.IGNORECASE)
        return prefix_pattern.sub("", title).strip()

    def _split_matchup(self, title: str):
        separators = [" vs. ", " vs ", " @ ", " at "]
        for sep in separators:
            if sep in title:
                parts = title.split(sep)
                if len(parts) == 2:
                    return parts[0].strip(), parts[1].strip()
        return None

    def _clean_team_name(self, name: str) -> str:
        name = name.strip()
        if ":" in name:
            prefix, rest = name.split(":", 1)
            if any(keyword in prefix.lower() for keyword in ("epl", "ucl", "soccer", "football")):
                name = rest.strip()
        
        # Remove " - More Markets"
        if " - More Markets" in name:
            name = name.replace(" - More Markets", "")
            
        # Remove trailing FC/AFC
        # Done in normalize_team_name, but good to do here for market matching
        if name.endswith(" FC"):
            name = name[:-3]
        elif name.endswith(" AFC"):
            name = name[:-4]
            
        return name.strip()

    def _find_winner_market(self, markets: List[Dict], title: str):
        for market in markets:
            if market.get("question") == title:
                return market

        for market in markets:
            question = market.get("question", "")
            if "win" in question.lower() and "draw" not in question.lower():
                return market

        return None

    def _parse_outcomes(self, market: Dict, away_team: str, home_team: str) -> List[Dict]:
        outcomes_raw = market.get("outcomes", "[]")
        prices_raw = market.get("outcomePrices", "[]")

        outcomes = json.loads(outcomes_raw) if isinstance(outcomes_raw, str) else outcomes_raw
        prices = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw

        if len(outcomes) < 2 or len(prices) < 2:
            return []

        outcome_data = []
        for outcome, price in zip(outcomes, prices):
            team_code = normalize_team_name(outcome, "polymarket")
            if team_code:
                outcome_data.append({
                    "code": team_code,
                    "raw_prob": float(price) * 100,
                })

        return outcome_data

    def _normalize_probabilities(self, outcome_data: List[Dict], away_code: str, home_code: str) -> Dict[str, int]:
        if len(outcome_data) < 2:
            return {}

        away_prob = 0
        home_prob = 0

        for item in outcome_data:
            if item["code"] == away_code:
                away_prob = item["raw_prob"]
            elif item["code"] == home_code:
                home_prob = item["raw_prob"]

        # Do not normalize for Soccer as it is a 3-way market (Win/Draw/Win)
        # Normalizing to 100% hides the Draw probability and causes false arbitrage detection
        return {
            away_code: away_prob,
            home_code: home_prob,
        }

if __name__ == '__main__':
    api = FootballPolymarketAPI()
    games = api.get_football_games()
    print(f"\\nFound {len(games)} football games:")
    for game in games[:5]:
        print(f"  {game['away_team']} @ {game['home_team']}: {game['away_prob']}% vs {game['home_prob']}%")
