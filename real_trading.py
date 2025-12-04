"""
Real Trading System for PolyMix
Executes live trades on Kalshi and Polymarket platforms
Includes comprehensive risk controls and error handling
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import requests
from typing import Dict, Tuple, Optional, List

REAL_TRADING_DATA_FILE = 'real_trading_data.json'


class PolymarketTradingClient:
    """Client for executing orders on Polymarket"""
    
    BASE_URL = "https://gamma-api.polymarket.com"
    
    def __init__(self, api_key: str = None, private_key: str = None):
        """
        Initialize Polymarket trading client
        Polymarket uses API key + private key for authentication
        """
        self.api_key = api_key or os.environ.get('POLYMARKET_API_KEY')
        self.private_key = private_key or os.environ.get('POLYMARKET_PRIVATE_KEY')
        self.session = requests.Session()
        self.session.timeout = 10
        self.session.headers.update({
            'User-Agent': 'PolyMix-RealTrader/1.0'
        })
        
    def place_order(self, market_id: str, side: str, amount: float, price: float) -> Dict:
        """
        Place an order on Polymarket
        
        Args:
            market_id: Market ID on Polymarket
            side: 'Yes' or 'No'
            amount: Amount to stake (in USD)
            price: Price to place order at (0-1 scale)
            
        Returns:
            Dict with order_id, status, and other details
        """
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'POLYMARKET_API_KEY not configured',
                    'order_id': None
                }
            
            # Create order payload
            payload = {
                'market': market_id,
                'side': side,  # 'Yes' or 'No'
                'amount': amount,
                'price': price,
                'orderType': 'limit'
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.BASE_URL}/orders"
            response = self.session.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'success': True,
                'order_id': data.get('id'),
                'status': data.get('status'),
                'filled': data.get('filled', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'order_id': None
            }
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order on Polymarket"""
        try:
            if not self.api_key:
                return {'success': False, 'error': 'POLYMARKET_API_KEY not configured'}
            
            headers = {'Authorization': f'Bearer {self.api_key}'}
            url = f"{self.BASE_URL}/orders/{order_id}"
            
            response = self.session.delete(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return {
                'success': True,
                'cancelled_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get status of an order"""
        try:
            if not self.api_key:
                return {'success': False, 'error': 'POLYMARKET_API_KEY not configured'}
            
            headers = {'Authorization': f'Bearer {self.api_key}'}
            url = f"{self.BASE_URL}/orders/{order_id}"
            
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'success': True,
                'status': data.get('status'),
                'filled': data.get('filled', 0),
                'remaining': data.get('remaining', 0),
                'average_price': data.get('average_price')
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_fills(self, market_id: str = None, limit: int = 100) -> List[Dict]:
        """Get list of filled orders"""
        try:
            if not self.api_key:
                return []
            
            headers = {'Authorization': f'Bearer {self.api_key}'}
            url = f"{self.BASE_URL}/fills"
            params = {'limit': limit}
            
            if market_id:
                params['market'] = market_id
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            fills = response.json().get('fills', [])
            return fills
            
        except Exception as e:
            print(f"Error fetching fills: {e}")
            return []


class KalshiTradingClient:
    """Client for executing orders on Kalshi"""
    
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    
    def __init__(self, api_key: str = None, secret: str = None):
        """
        Initialize Kalshi trading client
        Kalshi uses API key + secret for authentication
        """
        self.api_key = api_key or os.environ.get('KALSHI_API_KEY')
        self.secret = secret or os.environ.get('KALSHI_SECRET')
        self.session = requests.Session()
        self.session.timeout = 10
        self.session.headers.update({
            'User-Agent': 'PolyMix-RealTrader/1.0'
        })
        
    def place_order(self, ticker: str, side: str, amount: float, price: float, 
                    order_type: str = 'limit') -> Dict:
        """
        Place an order on Kalshi
        
        Args:
            ticker: Market ticker on Kalshi
            side: 'Yes' or 'No'
            amount: Amount to stake (in cents or units)
            price: Price to place order at
            order_type: 'limit' or 'market'
            
        Returns:
            Dict with order_id, status, and other details
        """
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'KALSHI_API_KEY not configured',
                    'order_id': None
                }
            
            # Create order payload
            payload = {
                'ticker': ticker,
                'side': side,  # 'Yes' or 'No'
                'count': int(amount),  # Kalshi uses count (shares)
                'price': int(price * 100),  # Convert to cents
                'type': order_type
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.BASE_URL}/orders"
            response = self.session.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json().get('order', {})
            return {
                'success': True,
                'order_id': data.get('order_id'),
                'status': data.get('status'),
                'filled': data.get('filled_count', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'order_id': None
            }
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order on Kalshi"""
        try:
            if not self.api_key:
                return {'success': False, 'error': 'KALSHI_API_KEY not configured'}
            
            headers = {'Authorization': f'Bearer {self.api_key}'}
            url = f"{self.BASE_URL}/orders/{order_id}"
            
            response = self.session.delete(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return {
                'success': True,
                'cancelled_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get status of an order"""
        try:
            if not self.api_key:
                return {'success': False, 'error': 'KALSHI_API_KEY not configured'}
            
            headers = {'Authorization': f'Bearer {self.api_key}'}
            url = f"{self.BASE_URL}/orders/{order_id}"
            
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json().get('order', {})
            return {
                'success': True,
                'status': data.get('status'),
                'filled': data.get('filled_count', 0),
                'remaining': data.get('count', 0) - data.get('filled_count', 0)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_fills(self, ticker: str = None, limit: int = 100) -> List[Dict]:
        """Get list of filled orders"""
        try:
            if not self.api_key:
                return []
            
            headers = {'Authorization': f'Bearer {self.api_key}'}
            url = f"{self.BASE_URL}/fills"
            params = {'limit': limit}
            
            if ticker:
                params['ticker'] = ticker
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            fills = response.json().get('fills', [])
            return fills
            
        except Exception as e:
            print(f"Error fetching fills: {e}")
            return []


class RealTradingSystem:
    """
    Real trading system that executes live trades
    Mirrors PaperTradingSystem interface but with actual API calls
    """
    
    def __init__(self):
        self.polymarket_client = PolymarketTradingClient()
        self.kalshi_client = KalshiTradingClient()
        self.load_data()
        
        # Risk controls
        try:
            self.daily_loss_limit = float(os.environ.get('LIVE_TRADING_DAILY_LOSS_LIMIT', 500))
        except:
            self.daily_loss_limit = 500.0
            
        try:
            self.max_position_size = float(os.environ.get('LIVE_TRADING_MAX_POSITION_SIZE', 1000))
        except:
            self.max_position_size = 1000.0
            
        try:
            self.max_daily_trades = int(os.environ.get('LIVE_TRADING_MAX_DAILY_TRADES', 10))
        except:
            self.max_daily_trades = 10
    
    def load_data(self):
        """Load trading data from persistent storage"""
        if os.path.exists(REAL_TRADING_DATA_FILE):
            try:
                with open(REAL_TRADING_DATA_FILE, 'r') as f:
                    self.data = json.load(f)
            except:
                self.reset_data()
        else:
            self.reset_data()
    
    def reset_data(self):
        """Initialize new trading data"""
        try:
            initial_balance = float(os.environ.get('LIVE_TRADING_INITIAL_BALANCE', 10000))
        except:
            initial_balance = 10000.0
        
        self.data = {
            'balance': initial_balance,
            'initial_balance': initial_balance,
            'bets': [],
            'total_profit': 0.0,
            'daily_trades': [],
            'daily_loss': 0.0,
            'errors': []
        }
        self.save_data()
    
    def save_data(self):
        """Save trading data to persistent storage"""
        with open(REAL_TRADING_DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)
    
    def get_state(self):
        """Get current trading state"""
        total_trades = len(self.data['bets'])
        total_profit = sum(bet.get('realized_profit', 0.0) for bet in self.data['bets'] if bet['status'] == 'settled')
        estimated_profit = sum(bet.get('profit', 0.0) for bet in self.data['bets'] if bet['status'] == 'pending')
        current_balance = self.data['balance']
        
        sorted_bets = sorted(self.data['bets'], key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'balance': current_balance,
            'initial_balance': self.data['initial_balance'],
            'total_profit': total_profit,
            'estimated_profit': estimated_profit,
            'total_trades': total_trades,
            'bets': sorted_bets,
            'daily_loss': self.data.get('daily_loss', 0.0),
            'daily_trades': len(self.data.get('daily_trades', []))
        }
    
    def _check_risk_controls(self, total_cost: float) -> Tuple[bool, str]:
        """Check if trade violates risk controls"""
        
        # Check daily trade limit
        today = datetime.now().date().isoformat()
        daily_trades = [t for t in self.data.get('daily_trades', []) 
                       if t.get('date') == today]
        if len(daily_trades) >= self.max_daily_trades:
            return False, f"Daily trade limit reached ({self.max_daily_trades})"
        
        # Check position size
        if total_cost > self.max_position_size:
            return False, f"Position size ({total_cost:.2f}) exceeds limit (${self.max_position_size:.2f})"
        
        # Check daily loss limit
        if self.data.get('daily_loss', 0.0) >= self.daily_loss_limit:
            return False, f"Daily loss limit reached (${self.daily_loss_limit:.2f})"
        
        # Check balance
        if total_cost > self.data['balance']:
            return False, "Insufficient balance"
        
        return True, "OK"
    
    def _normalize_risk_details(self, details):
        """Normalize risk details (same as PaperTradingSystem)"""
        if not details:
            return None
        
        if isinstance(details, dict) and 'bestAwayFrom' in details:
            normalized = details.copy()
            roi_percent = normalized.get('roiPercent')
            if roi_percent is not None and normalized.get('roi') is None:
                normalized['roi'] = roi_percent / 100
            if normalized.get('roi') is not None and normalized.get('roiPercent') is None:
                normalized['roiPercent'] = normalized['roi'] * 100
            return normalized
        
        if isinstance(details, dict) and 'best_away_platform' in details:
            roi_percent = details.get('roi_percent')
            return {
                'bestAwayFrom': details.get('best_away_platform'),
                'bestHomeFrom': details.get('best_home_platform'),
                'bestAwayPrice': details.get('best_away_price'),
                'bestHomePrice': details.get('best_home_price'),
                'bestAwayEffective': details.get('best_away_effective'),
                'bestHomeEffective': details.get('best_home_effective'),
                'totalCost': details.get('total_cost'),
                'edge': details.get('net_edge'),
                'grossCost': details.get('gross_cost'),
                'grossEdge': details.get('gross_edge'),
                'roiPercent': roi_percent,
                'roi': roi_percent / 100 if roi_percent is not None else None,
                'fees': details.get('fees', {})
            }
        
        return None
    
    def execute_arb(self, game, amount_per_leg=100.0) -> Tuple[bool, any]:
        """
        Execute a real arbitrage trade
        Reuses paper trading logic but makes actual API calls
        """
        
        # Check risk controls first
        risk_ok, risk_msg = self._check_risk_controls(amount_per_leg * 2)  # Rough estimate for 2 legs
        if not risk_ok:
            return False, risk_msg
        
        # Same arbitrage detection logic as PaperTradingSystem
        risk_detail = self._normalize_risk_details(game.get('riskFreeArb') or game.get('risk_free_arb'))
        required_keys = ['bestAwayPrice', 'bestHomePrice', 'bestAwayEffective', 'bestHomeEffective', 'totalCost', 'edge']
        if risk_detail and any(risk_detail.get(k) is None for k in required_keys):
            risk_detail = None
        
        # Check for zero prices
        if risk_detail:
            if risk_detail.get('bestAwayPrice', 0) <= 0 or risk_detail.get('bestHomePrice', 0) <= 0:
                return False, "Invalid odds (zero price detected)"
        
        if risk_detail and risk_detail.get('edge') and risk_detail.get('edge') > 0:
            poly = game.get('polymarket', {})
            kalshi = game.get('kalshi', {})
            
            if not poly or not kalshi:
                return False, "Missing platform data"
            
            try:
                target_units = float(os.environ.get('LIVE_TRADING_BET_AMOUNT', 100))
            except:
                target_units = 100.0
            
            quantity = target_units
            total_cost_usd = (risk_detail['totalCost'] / 100.0) * quantity
            profit_usd = (risk_detail['edge'] / 100.0) * quantity
            roi_percent = risk_detail.get('roiPercent', 0)
            
            try:
                min_roi = float(os.environ.get('LIVE_TRADING_MIN_ROI', 0))
            except:
                min_roi = 0.0
            
            if roi_percent <= min_roi:
                return False, f"ROI ({roi_percent:.2f}%) below threshold ({min_roi}%)"
            
            game_id = f"{game.get('away_code')}@{game.get('home_code')}"
            
            # Check for duplicate trades
            for bet in self.data['bets']:
                if bet['id'] == game_id and bet['status'] in ['pending', 'locked']:
                    return False, "Market already traded"
            
            # Prepare order details
            away_platform = risk_detail['bestAwayFrom']
            home_platform = risk_detail['bestHomeFrom']
            
            if away_platform == home_platform:
                return False, "Invalid arbitrage: both legs on same platform"
            
            best_away = {
                'platform': away_platform,
                'price': risk_detail['bestAwayPrice'],
                'eff': risk_detail['bestAwayEffective'],
                'team': game.get('away_team', 'Away'),
                'code': game.get('away_code'),
                'market_id': poly.get('away_market_id') or poly.get('market_id') if away_platform == 'Polymarket' else kalshi.get('away_ticker'),
                'url': poly.get('url', '') if away_platform == 'Polymarket' else kalshi.get('url', ''),
            }
            
            best_home = {
                'platform': home_platform,
                'price': risk_detail['bestHomePrice'],
                'eff': risk_detail['bestHomeEffective'],
                'team': game.get('home_team', 'Home'),
                'code': game.get('home_code'),
                'market_id': poly.get('home_market_id') or poly.get('market_id') if home_platform == 'Polymarket' else kalshi.get('home_ticker'),
                'url': poly.get('url', '') if home_platform == 'Polymarket' else kalshi.get('url', ''),
            }
            
            # Execute orders on both platforms
            trade = {
                'id': game_id,
                'game': f"{game.get('away_team')} vs {game.get('home_team')}",
                'sport': game.get('sport', 'unknown'),
                'timestamp': datetime.now().isoformat(),
                'game_time': game.get('game_time', '') or game.get('end_date', ''),
                'quantity': quantity,
                'cost': total_cost_usd,
                'payout': quantity * 1.0,
                'profit': profit_usd,
                'roi_percent': roi_percent,
                'status': 'pending',
                'legs': [best_away, best_home],
                'order_ids': {}
            }
            
            # Place away leg
            away_success = self._place_leg_order(best_away, quantity, trade)
            if not away_success:
                return False, "Failed to place away leg order"
            
            # Place home leg
            home_success = self._place_leg_order(best_home, quantity, trade)
            if not home_success:
                # Try to cancel away leg
                self._cancel_leg_order(best_away, trade)
                return False, "Failed to place home leg order"
            
            # Record trade
            self.data['bets'].append(trade)
            self.data['balance'] -= total_cost_usd
            
            today = datetime.now().date().isoformat()
            self.data['daily_trades'].append({
                'date': today,
                'id': game_id,
                'timestamp': datetime.now().isoformat()
            })
            
            self.save_data()
            return True, trade
        
        return False, "No risk-free arbitrage opportunity"
    
    def _place_leg_order(self, leg: Dict, quantity: float, trade: Dict) -> bool:
        """Place order for one leg of the arbitrage"""
        platform = None
        try:
            platform = leg.get('platform', 'Unknown')
            market_id = leg.get('market_id')
            price = leg['price'] / 100.0  # Convert cents to dollars
            team = leg.get('team', 'Unknown')
            
            if not market_id:
                error = f"Missing market ID for {platform} ({team})"
                self._record_error(trade['id'], error)
                print(f"❌ Order placement failed: {error}")
                return False
            
            print(f"Placing {platform} order for {team}: {quantity} @ ${price:.4f}")
            
            if platform == 'Polymarket':
                # Determine side (Yes/No) based on team code
                side = 'Yes'  # Default to Yes for away team
                
                result = self.polymarket_client.place_order(
                    market_id=market_id,
                    side=side,
                    amount=quantity,
                    price=price
                )
                
            elif platform == 'Kalshi':
                side = 'Yes'  # Default to Yes
                
                result = self.kalshi_client.place_order(
                    ticker=market_id,
                    side=side,
                    amount=quantity,
                    price=price
                )
            else:
                error = f"Unknown platform: {platform}"
                self._record_error(trade['id'], error)
                return False
            
            if result.get('success'):
                order_id = result.get('order_id')
                trade['order_ids'][platform] = order_id
                leg['order_id'] = order_id
                leg['order_status'] = result.get('status')
                print(f"✅ {platform} order placed: {order_id}")
                return True
            else:
                error = result.get('error', 'Order failed')
                self._record_error(trade['id'], error)
                print(f"❌ {platform} order failed: {error}")
                return False
                
        except Exception as e:
            error = f"Exception placing {platform or 'unknown'} order: {str(e)}"
            self._record_error(trade['id'], error)
            print(f"❌ {error}")
            return False
    
    def _cancel_leg_order(self, leg: Dict, trade: Dict):
        """Cancel an order"""
        try:
            order_id = leg.get('order_id')
            platform = leg['platform']
            
            if not order_id:
                return
            
            if platform == 'Polymarket':
                self.polymarket_client.cancel_order(order_id)
            elif platform == 'Kalshi':
                self.kalshi_client.cancel_order(order_id)
                
        except Exception as e:
            self._record_error(trade.get('id', 'unknown'), f"Cancel failed: {str(e)}")
    
    def _record_error(self, trade_id: str, error: str):
        """Record trading error"""
        self.data['errors'].append({
            'trade_id': trade_id,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
        # Keep only last 100 errors
        self.data['errors'] = self.data['errors'][-100:]
        self.save_data()
    
    def update_settlements(self, check_status_func) -> None:
        """
        Check pending trades and settle them
        Uses the same settlement logic as PaperTradingSystem
        """
        changed = False
        
        for bet in self.data['bets']:
            if bet['status'] == 'pending':
                all_legs_resolved = True
                total_payout = 0.0
                resolved_legs_count = 0
                
                for leg in bet['legs']:
                    platform = leg.get('platform')
                    market_id = leg.get('market_id')
                    
                    if not market_id:
                        continue
                    
                    status = check_status_func(platform, market_id)
                    
                    if not status.get('resolved'):
                        all_legs_resolved = False
                        break
                    
                    resolved_legs_count += 1
                    
                    winner = status.get('winner')
                    if str(winner) == str(leg.get('code')) or str(winner) == str(leg.get('team')):
                        total_payout += bet['quantity'] * 1.0
                
                if all_legs_resolved and resolved_legs_count == len(bet['legs']):
                    bet['status'] = 'settled'
                    bet['settled_amount'] = total_payout
                    bet['realized_profit'] = total_payout - bet['cost']
                    bet['profit'] = bet['realized_profit']
                    
                    self.data['balance'] += total_payout
                    
                    # Update daily loss tracking
                    if bet['realized_profit'] < 0:
                        self.data['daily_loss'] += abs(bet['realized_profit'])
                    
                    changed = True
                    print(f"Real Trade Settled: {bet['id']}. Payout: {total_payout}. Profit: {bet['realized_profit']}")
        
        if changed:
            self.save_data()
