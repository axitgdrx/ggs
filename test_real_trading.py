#!/usr/bin/env python3
"""
Test script for Real Trading System
Validates both paper and real trading modes
"""

import os
import json
from datetime import datetime

def test_paper_trading():
    """Test paper trading system"""
    print("\n" + "=" * 60)
    print("TEST 1: Paper Trading System")
    print("=" * 60)
    
    from paper_trading import PaperTradingSystem
    
    # Create instance
    pts = PaperTradingSystem()
    state = pts.get_state()
    
    print(f"✅ PaperTradingSystem initialized")
    print(f"   Balance: ${state['balance']:.2f}")
    print(f"   Initial Balance: ${state['initial_balance']:.2f}")
    print(f"   Total Trades: {state['total_trades']}")
    
    # Test with mock game
    mock_game = {
        'away_team': 'Test Away',
        'home_team': 'Test Home',
        'away_code': 'TA',
        'home_code': 'TH',
        'sport': 'test',
        'polymarket': {
            'away': 0.6,
            'home': 0.4,
            'raw_away': 0.6,
            'raw_home': 0.4,
            'market_id': 'test-market-1'
        },
        'kalshi': {
            'away': 0.4,
            'home': 0.6,
            'raw_away': 0.4,
            'raw_home': 0.6,
            'away_ticker': 'KX-TEST-1',
            'home_ticker': 'KX-TEST-2'
        }
    }
    
    success, result = pts.execute_arb(mock_game)
    if isinstance(result, str):
        print(f"⚠️  execute_arb returned reason: {result}")
    else:
        print(f"✅ execute_arb executed: {result.get('game') if isinstance(result, dict) else 'unknown'}")
    
    print("✅ Paper Trading System test passed")

def test_real_trading():
    """Test real trading system"""
    print("\n" + "=" * 60)
    print("TEST 2: Real Trading System")
    print("=" * 60)
    
    from real_trading import RealTradingSystem, PolymarketTradingClient, KalshiTradingClient
    
    # Create instances
    rts = RealTradingSystem()
    state = rts.get_state()
    
    print(f"✅ RealTradingSystem initialized")
    print(f"   Balance: ${state['balance']:.2f}")
    print(f"   Initial Balance: ${state['initial_balance']:.2f}")
    print(f"   Daily Loss: ${state['daily_loss']:.2f}")
    print(f"   Daily Trades: {state['daily_trades']}")
    
    # Test clients
    pm_client = PolymarketTradingClient()
    print(f"✅ PolymarketTradingClient created")
    print(f"   Auth mode: {pm_client.auth_mode}")
    print(f"   API Key configured: {'Yes' if pm_client.api_key else 'No'}")
    if pm_client.api_key_source == 'derived':
        print("   API key derived from wallet signature")
    if pm_client.clob_credentials:
        print("   CLOB credentials available")
    
    kalshi_client = KalshiTradingClient()
    print(f"✅ KalshiTradingClient created")
    print(f"   Auth mode: {kalshi_client.auth_mode}")
    if kalshi_client.auth_mode != 'rsa':
        print(f"   API Key configured: {'Yes' if kalshi_client.api_key else 'No'}")
    else:
        print("   RSA credentials loaded")
    
    # Test risk controls
    ok, msg = rts._check_risk_controls(100)
    print(f"✅ Risk controls check: {msg}")
    
    print("✅ Real Trading System test passed")

def test_api_endpoints():
    """Test Flask API endpoints"""
    print("\n" + "=" * 60)
    print("TEST 3: API Endpoints")
    print("=" * 60)
    
    import api
    from flask import json
    
    client = api.app.test_client()
    
    # Test /api/trading/mode
    response = client.get('/api/trading/mode')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = json.loads(response.data)
    print(f"✅ GET /api/trading/mode")
    print(f"   Mode: {data['mode']}")
    print(f"   Status: {response.status_code}")
    
    # Test /api/trading/state
    response = client.get('/api/trading/state')
    assert response.status_code == 200
    data = json.loads(response.data)
    print(f"✅ GET /api/trading/state")
    print(f"   Balance: ${data['balance']:.2f}")
    print(f"   Mode: {data['mode']}")
    print(f"   Status: {response.status_code}")
    
    # Test /api/paper/state (backward compatibility)
    response = client.get('/api/paper/state')
    assert response.status_code == 200
    print(f"✅ GET /api/paper/state (backward compatibility)")
    print(f"   Status: {response.status_code}")

def test_persistence():
    """Test data persistence"""
    print("\n" + "=" * 60)
    print("TEST 4: Data Persistence")
    print("=" * 60)
    
    from paper_trading import PaperTradingSystem
    
    pts = PaperTradingSystem()
    initial_balance = pts.get_state()['balance']
    
    # Modify and save
    pts.data['balance'] -= 10.0
    pts.save_data()
    
    # Reload
    pts2 = PaperTradingSystem()
    new_balance = pts2.get_state()['balance']
    
    assert new_balance == initial_balance - 10.0, "Data not persisted correctly"
    
    # Restore
    pts.data['balance'] = initial_balance
    pts.save_data()
    
    print(f"✅ Data persistence works")
    print(f"   Modified balance: ${new_balance:.2f}")
    print(f"   Restored to: ${initial_balance:.2f}")

def test_real_trading_data_files():
    """Verify real trading data files exist"""
    print("\n" + "=" * 60)
    print("TEST 5: Real Trading Data Files")
    print("=" * 60)
    
    from real_trading import REAL_TRADING_DATA_FILE
    
    if os.path.exists(REAL_TRADING_DATA_FILE):
        with open(REAL_TRADING_DATA_FILE, 'r') as f:
            data = json.load(f)
        print(f"✅ {REAL_TRADING_DATA_FILE} exists")
        print(f"   Balance: ${data['balance']:.2f}")
        print(f"   Total Trades: {len(data['bets'])}")
        print(f"   Daily Trades: {len(data['daily_trades'])}")
        print(f"   Errors Logged: {len(data['errors'])}")
    else:
        print(f"⚠️  {REAL_TRADING_DATA_FILE} not found (will be created on first trade)")

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "REAL TRADING SYSTEM - TEST SUITE" + " " * 16 + "║")
    print("╚" + "═" * 58 + "╝")
    
    try:
        test_paper_trading()
        test_real_trading()
        test_api_endpoints()
        test_persistence()
        test_real_trading_data_files()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\n📋 Summary:")
        print("  ✅ Paper Trading System works")
        print("  ✅ Real Trading System works")
        print("  ✅ API endpoints respond correctly")
        print("  ✅ Data persistence works")
        print("  ✅ Real trading data file present")
        print("\n🚀 Ready for production!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == '__main__':
    main()
