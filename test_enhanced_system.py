#!/usr/bin/env python3
"""
Test script to verify the enhanced arbitrage system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api import fetch_all_sports_data
from paper_trading import PaperTradingSystem

def test_enhanced_system():
    """Test the enhanced arbitrage detection system"""
    print("🚀 Testing Enhanced Arbitrage System")
    print("=" * 50)
    
    # Test 1: Fetch all sports data
    print("\n📊 Testing comprehensive data fetching...")
    try:
        data = fetch_all_sports_data(force_refresh=True)
        
        if data.get('success'):
            stats = data.get('stats', {})
            print(f"✅ Successfully fetched data:")
            print(f"   - Polymarket games: {stats.get('total_polymarket_games', 0)}")
            print(f"   - Kalshi games: {stats.get('total_kalshi_games', 0)}")
            print(f"   - Matched games: {stats.get('matched_games', 0)}")
            print(f"   - Arbitrage opportunities: {stats.get('arb_opportunities', 0)}")
            print(f"   - Match rate: {stats.get('match_rate', 0):.1f}%")
            
            # Check requirements
            matched = stats.get('matched_games', 0)
            arbs = stats.get('arb_opportunities', 0)
            
            print(f"\n🎯 Requirements Check:")
            print(f"   - Matched games ≥ 10: {'✅ PASS' if matched >= 10 else f'❌ FAIL ({matched} < 10)'}")
            print(f"   - Arbitrage opportunities ≥ 5: {'✅ PASS' if arbs >= 5 else f'❌ FAIL ({arbs} < 5)'}")
            
            if matched >= 10 and arbs >= 5:
                print("\n🎉 Requirements satisfied!")
            else:
                print("\n⚠️  Requirements not fully satisfied. System will continue searching...")
                
        else:
            print(f"❌ Failed to fetch data: {data.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
    
    # Test 2: Test enhanced arbitrage strategy
    print("\n💰 Testing enhanced arbitrage strategy...")
    try:
        trader = PaperTradingSystem()
        state = trader.get_state()
        
        print(f"   - Current balance: ${state.get('balance', 0):.2f}")
        print(f"   - Total trades: {state.get('total_trades', 0)}")
        print(f"   - Total profit: ${state.get('total_profit', 0):.2f}")
        print(f"   - Estimated profit: ${state.get('estimated_profit', 0):.2f}")
        
        # Show recent trades if any
        bets = state.get('bets', [])[:5]  # Show last 5 trades
        if bets:
            print(f"\n   Recent trades:")
            for i, bet in enumerate(bets):
                arb_type = bet.get('arb_type', 'unknown')
                profit = bet.get('profit', 0)
                roi = bet.get('roi_percent', 0)
                print(f"   {i+1}. {bet.get('game', 'Unknown')} - {arb_type} arb - ${profit:.2f} ({roi:.1f}% ROI)")
        else:
            print("   No trades yet - monitoring will start automatically")
            
    except Exception as e:
        print(f"❌ Error testing trading system: {e}")
    
    print("\n🔍 System Analysis Complete")
    print("=" * 50)

if __name__ == "__main__":
    test_enhanced_system()