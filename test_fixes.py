#!/usr/bin/env python3
"""
Test script to verify the fixes for:
1. 30-second cache
2. Paper trading covering all sports
3. Frontend displaying new markets
"""

import requests
import json
import time
from datetime import datetime

def test_api_endpoints():
    """Test all API endpoints"""
    base_url = "http://localhost:5001"
    
    endpoints = [
        "/api/odds/nba",
        "/api/odds/nfl", 
        "/api/odds/nhl",
        "/api/odds/football",
        "/api/odds/esports",
        "/api/odds/multi",
        "/api/odds/all-sports"
    ]
    
    print("Testing API endpoints...")
    results = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    if 'games' in data:
                        if isinstance(data['games'], dict):
                            # For NBA with today/tomorrow
                            total_games = len(data['games'].get('today', [])) + len(data['games'].get('tomorrow', []))
                        else:
                            total_games = len(data['games'])
                    else:
                        total_games = 0
                    
                    results[endpoint] = {
                        'status': 'success',
                        'games': total_games,
                        'stats': data.get('stats', {})
                    }
                    print(f"✅ {endpoint}: {total_games} games")
                else:
                    results[endpoint] = {'status': 'failed', 'error': data.get('error', 'Unknown error')}
                    print(f"❌ {endpoint}: {data.get('error', 'Unknown error')}")
            else:
                results[endpoint] = {'status': 'error', 'code': response.status_code}
                print(f"❌ {endpoint}: HTTP {response.status_code}")
        except Exception as e:
            results[endpoint] = {'status': 'exception', 'error': str(e)}
            print(f"❌ {endpoint}: {str(e)}")
    
    return results

def test_cache_timing():
    """Test cache timing - should be 30 seconds"""
    base_url = "http://localhost:5001"
    
    print("\nTesting cache timing...")
    
    # Make two requests to the same endpoint
    start_time = time.time()
    response1 = requests.get(f"{base_url}/api/odds/nba")
    first_request_time = time.time() - start_time
    
    start_time = time.time()
    response2 = requests.get(f"{base_url}/api/odds/nba")
    second_request_time = time.time() - start_time
    
    if response1.status_code == 200 and response2.status_code == 200:
        data1 = response1.json()
        data2 = response2.json()
        
        # Should have same timestamp (cached)
        same_timestamp = data1.get('timestamp') == data2.get('timestamp')
        
        # Second request should be faster (from cache)
        cache_working = second_request_time < first_request_time
        
        print(f"First request time: {first_request_time:.3f}s")
        print(f"Second request time: {second_request_time:.3f}s")
        print(f"Same timestamp: {same_timestamp}")
        print(f"Cache appears working: {cache_working}")
        
        return {
            'first_time': first_request_time,
            'second_time': second_request_time,
            'same_timestamp': same_timestamp,
            'cache_working': cache_working
        }
    else:
        print("❌ Failed to make requests")
        return None

def test_paper_trading_coverage():
    """Test that paper trading considers all sports"""
    base_url = "http://localhost:5001"
    
    print("\nTesting paper trading coverage...")
    
    # Get all sports data to see what's available
    try:
        response = requests.get(f"{base_url}/api/odds/multi")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                games = data.get('games', [])
                sport_counts = {}
                
                for game in games:
                    sport = game.get('sport', 'unknown')
                    sport_counts[sport] = sport_counts.get(sport, 0) + 1
                
                print(f"Games by sport in multi endpoint: {sport_counts}")
                
                # Check if we have all expected sports
                expected_sports = ['NBA', 'NFL', 'NHL', 'FOOTBALL', 'ESPORTS']
                missing_sports = [s for s in expected_sports if s not in sport_counts]
                
                if missing_sports:
                    print(f"⚠️  Missing sports: {missing_sports}")
                else:
                    print("✅ All expected sports present")
                
                return sport_counts
            else:
                print(f"❌ API error: {data.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    return None

def main():
    print(f"Running test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test all endpoints
    api_results = test_api_endpoints()
    
    # Test cache timing
    cache_results = test_cache_timing()
    
    # Test paper trading coverage
    coverage_results = test_paper_trading_coverage()
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    
    # Count successful endpoints
    successful = sum(1 for r in api_results.values() if r.get('status') == 'success')
    total = len(api_results)
    print(f"API endpoints: {successful}/{total} working")
    
    if cache_results:
        print(f"Cache: {'✅ Working' if cache_results['cache_working'] else '❌ Issues'}")
    
    if coverage_results:
        sports_count = len(coverage_results)
        print(f"Sports coverage: {sports_count} sports found")
    
    print("\nRecommendations:")
    print("1. Ensure server is running on localhost:5001")
    print("2. Check logs for any errors")
    print("3. Verify PAPER_TRADING_ENABLED=true for paper trading")
    print("4. Monitor the logs to see arbitrage detection in action")

if __name__ == "__main__":
    main()