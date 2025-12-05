# Real Trading System - Quick Start Guide

## 5-Minute Setup

### 1. Enable Real Trading in .env

```bash
# Edit .env file and add:
LIVE_TRADING=true
LIVE_TRADING_INITIAL_BALANCE=10000
LIVE_TRADING_BET_AMOUNT=100

# Add your platform API keys:
POLYMARKET_API_KEY=your_key_here
POLYMARKET_PRIVATE_KEY=your_private_key
KALSHI_API_KEY=your_key_here
KALSHI_SECRET=your_secret
```

### 2. Restart the Server

```bash
source .venv/bin/activate
python3 main.py
```

### 3. Verify It's Working

```bash
# Check if real trading is enabled
curl http://localhost:5001/api/trading/mode

# Should return:
# {
#   "live_trading_enabled": true,
#   "mode": "real",
#   "timestamp": "2024-01-15T10:30:00"
# }
```

## Important Safeguards

✅ **Already Built-In:**
- Daily loss limit (default: $500/day)
- Max position size (default: $1,000/trade)
- Max daily trades (default: 10/day)
- Min ROI threshold (default: 1%)
- Automatic order cancellation on failure
- Persistent error logging

## Monitoring

### Log Output
```
⚠️  LIVE TRADING ENABLED - Real trades will be executed!
Monitor job: Real Trading mode
Placing Polymarket order for Lakers: 100 @ $0.6500
✅ Polymarket order placed: order_123456
Placing Kalshi order for Celtics: 100 @ $0.3500
✅ Kalshi order placed: kalshi_789
🔴 LIVE 💰 New Arb: Lakers vs Celtics (+$25.50)
```

### Dashboard
Visit http://localhost:5001/paper to see real-time trading status

### State API
```bash
curl http://localhost:5001/api/trading/state
```

## Quick Reference

| Action | Endpoint | Method |
|--------|----------|--------|
| Check mode | `/api/trading/mode` | GET |
| Get state | `/api/trading/state` | GET |
| Reset data | `/api/trading/reset` | POST |

## Troubleshooting

### "Real trades will be executed" but orders not placed?
- Check API keys are set in .env
- Check market IDs are valid
- Check platform account has balance

### Daily limit reached early?
- Increase `LIVE_TRADING_MAX_DAILY_TRADES`
- Or wait until next day (UTC midnight)

### Lost all balance?
- Check `real_trading_data.json` for settlement details
- Verify actual outcomes on Polymarket/Kalshi
- Review error logs for issues

## Going Back to Paper Trading

```bash
# In .env, set:
LIVE_TRADING=false

# Restart server
python3 main.py
```

Your real trading data is preserved in `real_trading_data.json`

## Need Help?

1. **Check logs** in terminal output
2. **Review** `real_trading_data.json` for trade history
3. **Verify** orders on platform dashboards
4. **See** `REAL_TRADING_SETUP.md` for detailed documentation

---

⚠️ **Remember:** Real money is at risk. Start with small amounts and monitor carefully!
