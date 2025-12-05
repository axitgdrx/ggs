# Real Trading System Setup Guide

## Overview

PolyMix now supports both **Paper Trading** and **Real Trading** modes. The Real Trading System executes actual trades on Polymarket and Kalshi platforms while maintaining the same arbitrage detection and risk management logic.

## Architecture

### System Comparison

| Feature | Paper Trading | Real Trading |
|---------|--------------|-------------|
| Executes Real Orders | ❌ No | ✅ Yes |
| Risk Controls | ✅ Basic | ✅ Advanced |
| Daily Loss Limits | ✅ Tracked | ✅ Enforced |
| Position Size Limits | ⚠️ Manual | ✅ Automatic |
| Requires API Keys | ❌ No | ✅ Yes |
| Data Persistence | ✅ JSON | ✅ JSON |
| Settlement Checking | ✅ Yes | ✅ Yes |

### Key Components

1. **RealTradingSystem** (`real_trading.py`)
   - Main trading system class
   - Implements same interface as `PaperTradingSystem`
   - Manages trading state, risk controls, and settlements
   - Persists trades in `real_trading_data.json`

2. **PolymarketTradingClient** 
   - Executes orders on Polymarket
   - Methods: `place_order()`, `cancel_order()`, `get_order_status()`, `get_fills()`

3. **KalshiTradingClient**
   - Executes orders on Kalshi
   - Methods: `place_order()`, `cancel_order()`, `get_order_status()`, `get_fills()`

## Enabling Real Trading

### Step 1: Configure Environment Variables

Edit `.env` file and set:

```bash
# Enable Live Trading (⚠️ WARNING: This enables real trading!)
LIVE_TRADING=true

# Initial account balance (in USD)
LIVE_TRADING_INITIAL_BALANCE=10000

# Bet size per trade (in USD)
LIVE_TRADING_BET_AMOUNT=100

# Minimum ROI threshold (%)
LIVE_TRADING_MIN_ROI=1

# Risk Controls
LIVE_TRADING_MAX_POSITION_SIZE=1000      # Max USD per trade
LIVE_TRADING_MAX_DAILY_TRADES=10         # Max trades per day
LIVE_TRADING_DAILY_LOSS_LIMIT=500        # Max loss per day (USD)

# Platform API Keys (REQUIRED)
POLYMARKET_API_KEY=your_polymarket_key
POLYMARKET_PRIVATE_KEY=your_polymarket_private_key
KALSHI_API_KEY=your_kalshi_key
KALSHI_SECRET=your_kalshi_secret

# Reset Protection
LIVE_TRADING_RESET_KEY=your_secure_reset_key
```

### Step 2: Obtain API Keys

#### Polymarket
1. Go to https://polymarket.com
2. Go to Settings → API Keys
3. Create new API key
4. Copy `API Key` and `Private Key`

#### Kalshi
1. Go to https://kalshi.com
2. Go to Settings → API Keys
3. Create new API key
4. Copy `API Key` and `Secret`

### Step 3: Test Connection

The system will log:
```
⚠️  LIVE TRADING ENABLED - Real trades will be executed!
```

If you see this, real trading is enabled. Monitor logs during startup.

## Risk Controls

Real Trading System includes multiple layers of risk management:

### 1. Daily Loss Limit
- Tracks cumulative loss per day
- Stops new trades once limit is reached
- Resets at 00:00 UTC

### 2. Daily Trade Limit
- Limits number of trades per calendar day
- Default: 10 trades/day
- Prevents over-trading

### 3. Position Size Limit
- Maximum USD per individual trade
- Default: $1,000
- Prevents oversized positions

### 4. Minimum ROI Threshold
- Only trades with ROI > threshold
- Default: 1%
- Protects against marginal opportunities

### 5. Balance Check
- Verifies sufficient balance before each trade
- Prevents over-leveraging

## Monitoring

### Real-Time Logs

```bash
Monitor job: Real Trading mode
Fetching NBA, NFL, NHL data for paper trading...
Processing 50 games for arbitrage opportunities...
Placing Polymarket order for Lakers: 100 @ $0.6500
✅ Polymarket order placed: order_123456
Placing Kalshi order for Celtics: 100 @ $0.3500
✅ Kalshi order placed: kalshi_789
🔴 LIVE 💰 New Arb: Lakers vs Celtics (+$25.50)
```

### Trading State Endpoint

```bash
curl http://localhost:5001/api/trading/state
```

Response:
```json
{
  "balance": 9825.50,
  "initial_balance": 10000,
  "total_profit": 25.50,
  "estimated_profit": 15.25,
  "total_trades": 3,
  "daily_loss": 0,
  "daily_trades": 3,
  "mode": "real",
  "bets": [...]
}
```

### Trading Mode Endpoint

```bash
curl http://localhost:5001/api/trading/mode
```

## Safety Features

### 1. Settlement Verification
- Automatically checks market resolution every minute
- Updates profit/loss based on actual outcomes
- Handles both Polymarket and Kalshi settlement rules

### 2. Error Recovery
- Records all trading errors in `real_trading_data.json`
- Keeps last 100 errors for debugging
- Automatic order cancellation on failures

### 3. Order Atomicity
- If away leg succeeds but home leg fails:
  - Automatically cancels away leg
  - Returns error message
  - Logs for manual review

### 4. Confirmation Key Protection
- Reset endpoint requires `LIVE_TRADING_RESET_KEY`
- Prevents accidental data wipes

## Data Persistence

### Files Created

1. **real_trading_data.json**
   - Persistent trade history
   - Account balance tracking
   - Daily loss tracking
   - Error log

   Structure:
   ```json
   {
     "balance": 9850.00,
     "initial_balance": 10000,
     "bets": [
       {
         "id": "LAL@BOS",
         "game": "Lakers vs Celtics",
         "sport": "NBA",
         "timestamp": "2024-01-15T14:30:00",
         "status": "pending|settled",
         "legs": [...],
         "order_ids": {
           "Polymarket": "order_123",
           "Kalshi": "order_456"
         },
         "cost": 195.50,
         "profit": 25.50,
         ...
       }
     ],
     "daily_trades": [...],
     "daily_loss": 0.0,
     "errors": [...]
   }
   ```

## Switching Between Modes

### Paper → Real

1. Configure all API keys in `.env`
2. Set `LIVE_TRADING=true`
3. Restart application
4. Verify logs show: `⚠️  LIVE TRADING ENABLED`

### Real → Paper

1. Set `LIVE_TRADING=false`
2. Restart application
3. Verify logs show: `📄 Paper Trading Mode`
4. (Real trades already in `real_trading_data.json` are preserved)

## Best Practices

### Before Going Live

1. ✅ Test with small position sizes
2. ✅ Monitor first 24 hours actively
3. ✅ Verify settlement logic with manual checks
4. ✅ Set conservative daily loss limits
5. ✅ Document your API keys securely

### During Live Trading

1. 📊 Check dashboard every few hours
2. 📝 Monitor error logs regularly
3. 🔄 Verify settled trades match outcomes
4. 💰 Track daily P&L
5. 🚨 Act on errors immediately

### Emergency Procedures

If something goes wrong:

1. **Stop New Trades**
   - Set `LIVE_TRADING=false` immediately
   - Restart application

2. **Cancel Pending Orders**
   - Use platform dashboards
   - Or call `/api/trading/reset` (requires key)

3. **Review Trades**
   - Check `real_trading_data.json`
   - Verify platform order history
   - Identify discrepancies

## Troubleshooting

### API Key Error
```
LIVE_TRADING_ENABLED - Real trades will be executed!
...
Failed to place order: POLYMARKET_API_KEY not configured
```
**Solution:** Add `POLYMARKET_API_KEY` to `.env`

### Insufficient Balance
```
Failed to place order: Insufficient balance
```
**Solution:** Add funds to account or increase `LIVE_TRADING_INITIAL_BALANCE`

### Daily Limit Reached
```
No arb for Lakers vs Celtics: Daily trade limit reached (10)
```
**Solution:** Wait until next day or increase `LIVE_TRADING_MAX_DAILY_TRADES`

### Settlement Lag
Markets may take time to settle. Normal latency is 5-30 minutes after game end.

### Order Not Filled
Check platform dashboard to see if order is still pending or was rejected.

## Notifications

Real trades send push notifications with:
- 🔴 LIVE indicator
- Game details
- Profit estimate
- ROI percentage
- Timestamp

Example:
```
🔴 LIVE 💰 New Arb: Lakers vs Celtics
Mode: Real Trading
Sport: NBA
Type: perfect
Profit: $25.50
ROI: 12.75%
Cost: $200.00
```

## Performance Metrics

Monitor these metrics over time:

- **Win Rate**: % of settled trades that profit
- **Avg ROI**: Average return per trade
- **Total Trades**: Cumulative trades executed
- **Daily P&L**: Profit/loss by day
- **Max Drawdown**: Largest balance drop

## Support & Questions

For issues with:
- **API Connectivity**: Check platform status pages
- **Settlement Logic**: Review `check_trading_settlements()` in `api.py`
- **Risk Controls**: Adjust env variables and restart
- **Bug Reports**: Check `real_trading_data.json` error logs

---

⚠️ **DISCLAIMER**: Real trading involves actual money and real risk. Start with small amounts, monitor carefully, and only increase position sizes after confirming the system works correctly for your use case.
