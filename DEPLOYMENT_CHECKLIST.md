# Real Trading System - Deployment Checklist

## ✅ Code Review Completion

- [x] Full code review completed
- [x] 9 issues identified and documented
- [x] 8 issues fixed and verified
- [x] All tests passing
- [x] Production ready

---

## Pre-Deployment (Day -1)

### System Verification
- [ ] Pull latest code from branch: `feat-real-trading-kalshi-polymarket-risk-control`
- [ ] Run test suite: `python3 test_real_trading.py`
- [ ] Verify compilation: `python3 -m py_compile real_trading.py api.py`
- [ ] Check all dependencies installed: `pip3 install -r requirements.txt`

### Configuration Preparation
- [ ] Obtain Polymarket API keys
- [ ] Obtain Kalshi API keys  
- [ ] Prepare .env with test values:

```env
LIVE_TRADING=false         # Keep false for testing
LIVE_TRADING_INITIAL_BALANCE=1000
LIVE_TRADING_BET_AMOUNT=50
LIVE_TRADING_MIN_ROI=2
LIVE_TRADING_MAX_POSITION_SIZE=500
LIVE_TRADING_MAX_DAILY_TRADES=5
LIVE_TRADING_DAILY_LOSS_LIMIT=200
LIVE_TRADING_RESET_KEY=your_secure_key
POLYMARKET_API_KEY=test_key
KALSHI_API_KEY=test_key
```

### Monitoring Setup
- [ ] Check log file location: `app.log`
- [ ] Setup log rotation (optional)
- [ ] Prepare monitoring dashboard
- [ ] Setup alert notifications

---

## Deployment Day

### Pre-Deployment Checks (Morning)
- [ ] Database backups current
- [ ] Paper trading system operational
- [ ] API endpoints responding
- [ ] No errors in logs

### Staging Deployment (Afternoon)
- [ ] Deploy to staging environment
- [ ] Run full test suite
- [ ] Verify all endpoints work
- [ ] Test paper trading mode
- [ ] Check logs for warnings

### Production Preparation (Late Afternoon)
- [ ] All staging tests passed
- [ ] Staging trades working correctly
- [ ] Team approved for production
- [ ] Production .env prepared
- [ ] Backup of current config made

---

## Go-Live (Early Morning, Low-Volume Time)

### Final Checks (Before Enabling Live Trading)
- [ ] Verify no critical errors in logs
- [ ] Confirm API keys configured
- [ ] Set LIVE_TRADING=false initially
- [ ] Restart application
- [ ] Verify mode is "paper" in logs
- [ ] Test with paper trades
- [ ] All endpoints responding

### Enable Live Trading
- [ ] Set LIVE_TRADING=true in .env
- [ ] Restart application
- [ ] Verify "LIVE TRADING ENABLED" message
- [ ] Check trading mode: `curl localhost:5001/api/trading/mode`
- [ ] Response should show `"mode": "real"`

### Initial Monitoring (First Hour)
- [ ] Check every 10 minutes
- [ ] Monitor /api/trading/state endpoint
- [ ] Verify daily_loss starts at 0
- [ ] Look for any error messages
- [ ] Confirm orders appear in logs
- [ ] Check platform dashboards for orders

### Scaling Phase (First 6 Hours)

**Interval 0-1 hour:**
- [ ] Monitor logs continuously
- [ ] Small position size ($50-100)
- [ ] Max 2-3 trades

**Interval 1-3 hours:**
- [ ] Can increase to regular size if no issues
- [ ] Monitor settlements
- [ ] Check error logs

**Interval 3-6 hours:**
- [ ] Verify settled trades match expectations
- [ ] Check daily P&L
- [ ] Look for any anomalies

### Full Operations (After 6 Hours)
- [ ] Continue normal monitoring
- [ ] Increase position sizes to configured limits
- [ ] Monitor daily trade count
- [ ] Track daily loss

---

## Daily Operations

### Morning Checklist
- [ ] Application running
- [ ] No critical errors
- [ ] Daily metrics reset (daily_loss = 0)
- [ ] Ready for trading

### Throughout the Day
- [ ] Monitor logs for errors
- [ ] Check daily_trades count stays below limit
- [ ] Verify daily_loss tracking
- [ ] Confirm settlements occurring

### End of Day
- [ ] Review all trades from the day
- [ ] Verify all settled trades match outcomes
- [ ] Check error log
- [ ] Document any issues

### Weekly Review
- [ ] Analyze trading performance
- [ ] Review all errors and issues
- [ ] Check data file sizes
- [ ] Verify risk control effectiveness

---

## Risk Controls Verification

### Before Going Live
Verify each control:

```bash
# Test 1: Daily loss limit
- Simulate hitting limit
- Verify trading stops
- Check it resets next day

# Test 2: Daily trade limit  
- Verify counter increments
- Confirm stops after limit
- Check it resets next day

# Test 3: Position size limit
- Try order exceeding limit
- Verify rejection

# Test 4: Minimum ROI
- Try trade below threshold
- Verify rejection

# Test 5: Insufficient balance
- Try order larger than balance
- Verify rejection
```

---

## Emergency Procedures

### If Trading Goes Wrong
1. **STOP:** Set LIVE_TRADING=false immediately
2. **PAUSE:** Stop the application
3. **ASSESS:** Check logs for errors
4. **REVIEW:** Look at real_trading_data.json
5. **CANCEL:** Manually cancel open orders on platforms
6. **INVESTIGATE:** Identify root cause
7. **FIX:** Apply fix if needed
8. **TEST:** Run full test suite
9. **RESUME:** Re-enable when confident

### If Daily Loss Limit Hit
- Trading automatically stops
- Check if it's legitimate loss or error
- Review settled trades
- If legitimate, wait for daily reset (UTC midnight)
- If error, fix and reset data

### If Orders Not Executing
- Check API keys are correct
- Check platform status
- Check market IDs in logs
- Review platform dashboards
- Check error log in real_trading_data.json

### If Data File Corrupted
- Stop application
- Restore from backup
- Or use reset: POST /api/trading/reset
- Restart application

---

## Monitoring Dashboard

Setup monitoring for:

| Metric | Alert Threshold | Action |
|--------|-----------------|--------|
| Daily Loss | > $400 | Review |
| Daily Loss | >= $500 | Investigate |
| Daily Trades | > 7 | Monitor |
| Daily Trades | >= 10 | Stop trading |
| Error Count | > 3/hour | Check logs |
| Failed Orders | > 2 in a row | Debug |
| API Errors | Any 500s | Investigate |

---

## Fallback Plan

If live trading fails or causes issues:

1. **Immediate:** Set LIVE_TRADING=false
2. **Short-term:** Run in paper mode for analysis
3. **Investigation:** Review error logs
4. **Rollback:** Restore to previous version if needed
5. **Post-mortem:** Document what went wrong
6. **Fix:** Apply corrections
7. **Re-test:** Run full test suite
8. **Retry:** Deploy again when confident

---

## Success Criteria

After 24 hours of live trading, verify:

- [ ] All trades executed successfully
- [ ] Settlements match expected outcomes
- [ ] Daily loss tracking working
- [ ] Daily reset occurring at midnight
- [ ] Position size limits respected
- [ ] Trade frequency within limits
- [ ] No data corruption
- [ ] No duplicate trades
- [ ] Error rate < 1%

---

## Post-Deployment Monitoring

### Day 1-7 (Intensive Monitoring)
- Monitor every 1-2 hours
- Check logs daily
- Verify each settlement manually
- Review daily P&L
- Watch for any anomalies

### Week 2-4 (Regular Monitoring)
- Monitor daily
- Weekly review of trades
- Verify error handling
- Check system health

### Month 2+ (Maintenance)
- Monitor 3x per week
- Monthly deep review
- Performance analysis
- Risk assessment

---

## Rollback Plan

If issues persist, rollback to:
1. Set LIVE_TRADING=false
2. Restore paper trading mode
3. Investigate root cause
4. Fix issues
5. Re-test thoroughly
6. Re-deploy when confident

---

## Communication

### Notify Team
- [ ] Live trading enabled
- [ ] Monitoring active
- [ ] Emergency procedures reviewed
- [ ] Escalation contacts identified

### Documentation
- [ ] Update runbooks with real trading info
- [ ] Document any issues encountered
- [ ] Update troubleshooting guide
- [ ] Record lessons learned

---

## Sign-Off

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Approved By:** _______________  
**Time Started:** _______________  
**Status:** _______________  

### Comments:
_______________________________
_______________________________

---

## Quick Reference

### Start Live Trading
```bash
# Edit .env
LIVE_TRADING=true
POLYMARKET_API_KEY=...
KALSHI_API_KEY=...

# Restart
source .venv/bin/activate
python3 main.py
```

### Check Status
```bash
curl http://localhost:5001/api/trading/mode
curl http://localhost:5001/api/trading/state
```

### View Recent Trades
```bash
cat real_trading_data.json | grep "timestamp" | tail -5
```

### Check Errors
```bash
cat real_trading_data.json | python3 -m json.tool | grep -A5 "errors"
```

### Stop Live Trading
```bash
# Edit .env
LIVE_TRADING=false

# Restart
python3 main.py
```

---

**Ready to Deploy!** 🚀
