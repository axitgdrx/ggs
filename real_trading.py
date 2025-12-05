"""
Real Trading System for PolyMix
Executes live trades on Kalshi and Polymarket platforms
Includes comprehensive risk controls and error handling
"""

import base64
import json
import os
import time
import hmac
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict

import requests
from typing import Dict, Tuple, Optional, List, Any

from eth_account import Account
from eth_account.messages import encode_structured_data
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

REAL_TRADING_DATA_FILE = 'real_trading_data.json'


class PolymarketClobAuthenticator:
    """Handles Polymarket CLOB authentication via wallet signatures."""

    DOMAIN_NAME = "ClobAuthDomain"
    DOMAIN_VERSION = "1"
    MESSAGE = "This message attests that I control the given wallet"

    def __init__(self, private_key: str, chain_id: int = 137,
                 base_url: str = "https://clob.polymarket.com",
                 session: Optional[requests.Session] = None):
        if not private_key:
            raise ValueError("Polymarket private key is required for CLOB authentication")
        self.private_key = self._normalize_private_key(private_key)
        self.chain_id = chain_id
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.account = Account.from_key(self.private_key)
        self.creds: Optional[Dict[str, str]] = None

    def _normalize_private_key(self, key: str) -> str:
        key = key.strip()
        if not key:
            raise ValueError("Empty private key provided")
        if not key.startswith("0x"):
            key = f"0x{key}"
        return key

    def _build_structured_data(self, timestamp: int, nonce: int) -> Dict[str, Any]:
        return {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                ],
                "ClobAuth": [
                    {"name": "address", "type": "address"},
                    {"name": "timestamp", "type": "string"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "message", "type": "string"},
                ],
            },
            "domain": {
                "name": self.DOMAIN_NAME,
                "version": self.DOMAIN_VERSION,
                "chainId": self.chain_id,
            },
            "primaryType": "ClobAuth",
            "message": {
                "address": self.account.address,
                "timestamp": str(timestamp),
                "nonce": int(nonce),
                "message": self.MESSAGE,
            },
        }

    def _sign_auth_payload(self, timestamp: int, nonce: int) -> str:
        structured = self._build_structured_data(timestamp, nonce)
        signable = encode_structured_data(structured)
        signed = Account.sign_message(signable, self.private_key)
        return signed.signature.hex()

    def _build_l1_headers(self, nonce: int = 0, timestamp: Optional[int] = None) -> Dict[str, str]:
        ts = int(timestamp or time.time())
        signature = self._sign_auth_payload(ts, nonce)
        return {
            'POLY_ADDRESS': self.account.address,
            'POLY_SIGNATURE': signature,
            'POLY_TIMESTAMP': str(ts),
            'POLY_NONCE': str(nonce),
        }

    def _format_body(self, body: Any) -> Optional[str]:
        if body is None:
            return None
        if isinstance(body, str):
            return body
        return json.dumps(body, separators=(',', ':'), ensure_ascii=False)

    def _build_l2_headers(self, method: str, endpoint: str, body: Any = None,
                          timestamp: Optional[int] = None) -> Dict[str, str]:
        creds = self.ensure_credentials()
        ts = int(timestamp or time.time())
        body_str = self._format_body(body)
        message = f"{ts}{method.upper()}{endpoint}"
        if body_str:
            message += body_str
        secret = base64.b64decode(creds['secret'])
        digest = hmac.new(secret, message.encode('utf-8'), hashlib.sha256).digest()
        signature = base64.b64encode(digest).decode('utf-8').replace('+', '-').replace('/', '_')
        return {
            'POLY_ADDRESS': self.account.address,
            'POLY_SIGNATURE': signature,
            'POLY_TIMESTAMP': str(ts),
            'POLY_API_KEY': creds['key'],
            'POLY_PASSPHRASE': creds['passphrase'],
        }

    def _handle_api_response(self, response: requests.Response) -> Dict[str, str]:
        response.raise_for_status()
        data = response.json()
        if {'apiKey', 'secret', 'passphrase'}.issubset(data.keys()):
            creds = {
                'key': data['apiKey'],
                'secret': data['secret'],
                'passphrase': data['passphrase'],
            }
            self.creds = creds
            return creds
        return data

    def create_api_key(self) -> Dict[str, str]:
        endpoint = f"{self.base_url}/auth/api-key"
        headers = self._build_l1_headers()
        response = self.session.post(endpoint, headers=headers, timeout=10)
        return self._handle_api_response(response)

    def derive_api_key(self) -> Dict[str, str]:
        endpoint = f"{self.base_url}/auth/derive-api-key"
        headers = self._build_l1_headers()
        response = self.session.get(endpoint, headers=headers, timeout=10)
        return self._handle_api_response(response)

    def ensure_credentials(self) -> Dict[str, str]:
        if self.creds:
            return self.creds
        try:
            creds = self.create_api_key()
        except Exception:
            creds = None
        if not isinstance(creds, dict) or 'key' not in creds:
            creds = self.derive_api_key()
        if not isinstance(creds, dict) or 'key' not in creds:
            raise RuntimeError('Unable to obtain Polymarket API credentials')
        self.creds = creds
        return creds

    def request(self, method: str, endpoint: str, payload: Any = None,
                params: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Any:
        if not endpoint.startswith('/'):
            endpoint = f'/{endpoint}'
        method = method.upper()
        headers = self._build_l2_headers(method, endpoint, payload)
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, headers=headers, json=payload,
                                            params=params, timeout=timeout)
            response.raise_for_status()
            if response.content:
                return response.json()
            return {}
        except requests.RequestException as exc:
            error_text = exc.response.text if exc.response is not None else str(exc)
            raise RuntimeError(f"Polymarket CLOB request failed: {error_text}") from exc

    def get_credentials(self) -> Optional[Dict[str, str]]:
        return self.creds


class PolymarketTradingClient:
    """Client for executing orders on Polymarket"""
    
    BASE_URL = "https://gamma-api.polymarket.com"
    
    def __init__(self, api_key: str = None, private_key: str = None):
        """Initialize Polymarket trading client."""
        self.session = requests.Session()
        self.session.timeout = 10
        self.session.headers.update({'User-Agent': 'PolyMix-RealTrader/1.0'})
        self.api_key = api_key or os.environ.get('POLYMARKET_API_KEY')
        self.api_key_source = 'env' if self.api_key else None
        raw_private_key = private_key or os.environ.get('POLYMARKET_PRIVATE_KEY')
        self.clob_auth: Optional[PolymarketClobAuthenticator] = None
        self.clob_credentials: Optional[Dict[str, str]] = None
        self.auth_mode = 'api-key' if self.api_key else 'unconfigured'

        if raw_private_key:
            try:
                chain_id = int(os.environ.get('POLYMARKET_CHAIN_ID', 137))
            except Exception:
                chain_id = 137
            clob_base = os.environ.get('POLYMARKET_CLOB_URL', 'https://clob.polymarket.com')
            try:
                self.clob_auth = PolymarketClobAuthenticator(
                    raw_private_key,
                    chain_id=chain_id,
                    base_url=clob_base,
                    session=self.session,
                )
                self.clob_credentials = self.clob_auth.ensure_credentials()
                if not self.api_key and self.clob_credentials:
                    self.api_key = self.clob_credentials.get('key')
                    self.api_key_source = 'derived'
                self.auth_mode = 'clob'
            except Exception as exc:
                print(f"Failed to initialize Polymarket CLOB authentication: {exc}")

    def clob_request(self, method: str, endpoint: str, payload: Any = None,
                     params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a signed request against the Polymarket CLOB API."""
        if not self.clob_auth:
            return {'success': False, 'error': 'Polymarket CLOB authentication is not configured'}
        try:
            data = self.clob_auth.request(method, endpoint, payload=payload, params=params)
            return {'success': True, 'data': data}
        except Exception as exc:
            return {'success': False, 'error': str(exc)}

    def get_clob_credentials(self) -> Optional[Dict[str, str]]:
        if self.clob_credentials:
            return self.clob_credentials
        if not self.clob_auth:
            return None
        try:
            self.clob_credentials = self.clob_auth.ensure_credentials()
            return self.clob_credentials
        except Exception:
            return None

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
    """Client for executing orders on Kalshi."""

    BASE_URL = "https://api.kalshi.com/trade-api/v2"
    SIGNING_PREFIX = "/trade-api/v2"

    def __init__(self, api_key: str = None, secret: str = None,
                 api_key_id: str = None, private_key: str = None,
                 private_key_path: str = None):
        self.session = requests.Session()
        self.session.timeout = 10
        self.session.headers.update({'User-Agent': 'PolyMix-RealTrader/1.0'})
        self.api_key = api_key or os.environ.get('KALSHI_API_KEY')
        self.secret = secret or os.environ.get('KALSHI_SECRET')
        self.api_key_id = api_key_id or os.environ.get('KALSHI_API_KEY_ID')
        self.private_key_str = private_key or os.environ.get('KALSHI_PRIVATE_KEY')
        self.private_key_path = private_key_path or os.environ.get('KALSHI_PRIVATE_KEY_PATH')
        self._rsa_private_key = None
        self.base_url = (os.environ.get('KALSHI_API_URL') or self.BASE_URL).rstrip('/')
        self.auth_mode = 'api-key' if self.api_key else 'unconfigured'

        if self.api_key_id and (self.private_key_str or self.private_key_path):
            try:
                self._rsa_private_key = self._load_private_key()
                self.auth_mode = 'rsa'
            except Exception as exc:
                print(f"Failed to initialize Kalshi RSA authentication: {exc}")
        elif self.api_key:
            self.auth_mode = 'api-key'

    def _load_private_key(self):
        if self.private_key_str:
            pem_data = self.private_key_str.replace('\\n', '\n').encode('utf-8')
        elif self.private_key_path:
            with open(self.private_key_path, 'rb') as key_file:
                pem_data = key_file.read()
        else:
            raise ValueError('Kalshi private key is not configured')
        return serialization.load_pem_private_key(pem_data, password=None)

    def _signed_headers(self, method: str, endpoint: str) -> Dict[str, str]:
        if not self._rsa_private_key or not self.api_key_id:
            raise RuntimeError('Kalshi RSA credentials are not configured')
        timestamp = str(int(time.time() * 1000))
        payload = f"{timestamp}{method.upper()}{self.SIGNING_PREFIX}{endpoint}"
        signature = self._rsa_private_key.sign(
            payload.encode('utf-8'),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        return {
            'KALSHI-ACCESS-KEY': self.api_key_id,
            'KALSHI-ACCESS-TIMESTAMP': timestamp,
            'KALSHI-ACCESS-SIGNATURE': signature_b64,
            'Content-Type': 'application/json'
        }

    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None,
                 payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not endpoint.startswith('/'):
            endpoint = f'/{endpoint}'
        url = f"{self.base_url}{endpoint}"
        headers = None
        if self.auth_mode == 'rsa' and self._rsa_private_key:
            headers = self._signed_headers(method, endpoint)
        elif self.api_key:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
        else:
            return {'success': False, 'error': 'Kalshi credentials not configured'}
        try:
            response = self.session.request(method, url, headers=headers, params=params,
                                            json=payload, timeout=10)
            if response.status_code >= 400:
                return {'success': False, 'error': response.text, 'status': response.status_code}
            data = response.json() if response.content else {}
            return {'success': True, 'data': data}
        except Exception as exc:
            return {'success': False, 'error': str(exc)}

    def place_order(self, ticker: str, side: str, amount: float, price: float,
                    order_type: str = 'limit') -> Dict[str, Any]:
        payload = {
            'ticker': ticker,
            'side': side,
            'count': int(amount),
            'price': int(price * 100),
            'type': order_type
        }
        result = self._request('POST', '/orders', payload=payload)
        if not result.get('success'):
            return {**result, 'order_id': None}
        data = result['data'].get('order', {})
        return {
            'success': True,
            'order_id': data.get('order_id'),
            'status': data.get('status'),
            'filled': data.get('filled_count', 0),
            'timestamp': datetime.now().isoformat()
        }

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        result = self._request('DELETE', f'/orders/{order_id}')
        if not result.get('success'):
            return result
        return {'success': True, 'cancelled_at': datetime.now().isoformat()}

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        result = self._request('GET', f'/orders/{order_id}')
        if not result.get('success'):
            return result
        data = result['data'].get('order', {})
        return {
            'success': True,
            'status': data.get('status'),
            'filled': data.get('filled_count', 0),
            'remaining': data.get('count', 0) - data.get('filled_count', 0)
        }

    def get_fills(self, ticker: str = None, limit: int = 100) -> List[Dict]:
        params: Dict[str, Any] = {'limit': limit}
        if ticker:
            params['ticker'] = ticker
        result = self._request('GET', '/fills', params=params)
        if not result.get('success'):
            print(f"Error fetching fills: {result.get('error')}")
            return []
        return result['data'].get('fills', [])


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
                
                # Migrate old data format if needed
                today = datetime.now().date().isoformat()
                if 'last_daily_reset_date' not in self.data:
                    self.data['last_daily_reset_date'] = today
                if 'daily_loss' not in self.data:
                    self.data['daily_loss'] = 0.0
                if 'daily_trades' not in self.data:
                    self.data['daily_trades'] = []
                if 'errors' not in self.data:
                    self.data['errors'] = []
                    
            except Exception as e:
                print(f"Error loading trading data: {e}. Resetting...")
                self.reset_data()
        else:
            self.reset_data()
    
    def reset_data(self):
        """Initialize new trading data"""
        try:
            initial_balance = float(os.environ.get('LIVE_TRADING_INITIAL_BALANCE', 10000))
        except:
            initial_balance = 10000.0
        
        today = datetime.now().date().isoformat()
        
        self.data = {
            'balance': initial_balance,
            'initial_balance': initial_balance,
            'bets': [],
            'total_profit': 0.0,
            'daily_trades': [],
            'daily_loss': 0.0,
            'last_daily_reset_date': today,
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
        
        today = datetime.now().date().isoformat()
        
        # Reset daily metrics if date changed (daily reset at UTC midnight)
        last_reset_date = self.data.get('last_daily_reset_date')
        if last_reset_date != today:
            self.data['daily_loss'] = 0.0
            self.data['daily_trades'] = []
            self.data['last_daily_reset_date'] = today
            # Don't save here; let caller decide
        
        # Check daily trade limit
        daily_trades = [t for t in self.data.get('daily_trades', []) 
                       if t.get('date') == today]
        if len(daily_trades) >= self.max_daily_trades:
            return False, f"Daily trade limit reached ({self.max_daily_trades})"
        
        # Check position size
        if total_cost > self.max_position_size:
            return False, f"Position size ({total_cost:.2f}) exceeds limit (${self.max_position_size:.2f})"
        
        # Check daily loss limit
        current_daily_loss = self.data.get('daily_loss', 0.0)
        if current_daily_loss >= self.daily_loss_limit:
            return False, f"Daily loss limit reached (${self.daily_loss_limit:.2f}), current: ${current_daily_loss:.2f}"
        
        # Check balance
        if total_cost > self.data['balance']:
            return False, f"Insufficient balance: ${self.data['balance']:.2f} < ${total_cost:.2f}"
        
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
            
            # Check risk controls AFTER computing actual cost (not just estimate)
            risk_ok, risk_msg = self._check_risk_controls(total_cost_usd)
            if not risk_ok:
                return False, risk_msg
            
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
            
            # Extract market IDs with fallback options
            away_market_id = None
            if away_platform == 'Polymarket':
                away_market_id = poly.get('away_market_id') or poly.get('market_id')
            else:  # Kalshi
                away_market_id = kalshi.get('away_ticker') or kalshi.get('away_market_id')
            
            home_market_id = None
            if home_platform == 'Polymarket':
                home_market_id = poly.get('home_market_id') or poly.get('market_id')
            else:  # Kalshi
                home_market_id = kalshi.get('home_ticker') or kalshi.get('home_market_id')
            
            # Validate market IDs
            if not away_market_id:
                return False, f"Missing market ID for {away_platform} (away leg)"
            if not home_market_id:
                return False, f"Missing market ID for {home_platform} (home leg)"
            
            best_away = {
                'platform': away_platform,
                'price': risk_detail['bestAwayPrice'],
                'eff': risk_detail['bestAwayEffective'],
                'team': game.get('away_team', 'Away'),
                'code': game.get('away_code'),
                'market_id': away_market_id,
                'url': poly.get('url', '') if away_platform == 'Polymarket' else kalshi.get('url', ''),
            }
            
            best_home = {
                'platform': home_platform,
                'price': risk_detail['bestHomePrice'],
                'eff': risk_detail['bestHomeEffective'],
                'team': game.get('home_team', 'Home'),
                'code': game.get('home_code'),
                'market_id': home_market_id,
                'url': poly.get('url', '') if home_platform == 'Polymarket' else kalshi.get('url', ''),
            }
            
            # Validate order parameters
            if quantity <= 0:
                return False, f"Invalid quantity: {quantity} (must be > 0)"
            if not (0 < best_away['price'] < 1):
                return False, f"Invalid away price: {best_away['price']} (must be between 0 and 1)"
            if not (0 < best_home['price'] < 1):
                return False, f"Invalid home price: {best_home['price']} (must be between 0 and 1)"
            
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
                # Try to cancel away leg (important for atomicity)
                self._cancel_leg_order(best_away, trade)
                return False, "Failed to place home leg order (away leg cancelled)"
            
            # Record trade with error handling
            try:
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
            except Exception as e:
                # Rollback: remove trade if save fails
                if self.data['bets'] and self.data['bets'][-1]['id'] == game_id:
                    self.data['bets'].pop()
                    self.data['balance'] += total_cost_usd
                
                error_msg = f"Failed to save trade: {str(e)}"
                self._record_error(game_id, error_msg)
                return False, error_msg
        
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
                    # All legs resolved - settle the trade
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
                
                elif not all_legs_resolved and resolved_legs_count > 0:
                    # Some legs resolved but not all - check timeout (24 hours)
                    trade_age = datetime.now() - datetime.fromisoformat(bet['timestamp'])
                    if trade_age.total_seconds() > 86400:  # 24 hours
                        bet['status'] = 'incomplete'
                        bet['settled_amount'] = total_payout
                        bet['realized_profit'] = total_payout - bet['cost']
                        bet['profit'] = bet['realized_profit']
                        
                        self.data['balance'] += total_payout
                        
                        # Track any loss
                        if bet['realized_profit'] < 0:
                            self.data['daily_loss'] += abs(bet['realized_profit'])
                        
                        changed = True
                        print(f"Real Trade Marked Incomplete (timeout): {bet['id']}. Partial payout: {total_payout}. Profit: {bet['realized_profit']}")
        
        if changed:
            self.save_data()
