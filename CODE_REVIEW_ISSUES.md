# Real Trading System - Code Review Issues Found

## Critical Issues

### 1. ⚠️ CRITICAL: Daily Loss Limit Never Resets
**Location:** `real_trading.py` - `_check_risk_controls()` and `update_settlements()`
**Problem:** 
- `daily_loss` is accumulated but never resets at midnight/UTC
- This means once the daily loss limit is hit, trading is blocked forever (or until manual reset)
- The check at line 396: `if self.data.get('daily_loss', 0.0) >= self.daily_loss_limit:` becomes permanently true

**Impact:** BLOCKS ALL TRADING once daily loss limit hit
**Severity:** CRITICAL - Breaks trading system functionality

**Fix:** Add date tracking and daily reset mechanism
```python
def _check_risk_controls(self, total_cost: float) -> Tuple[bool, str]:
    today = datetime.now().date().isoformat()
    
    # Reset daily metrics if date changed
    if self.data.get('last_daily_reset_date') != today:
        self.data['daily_loss'] = 0.0
        self.data['daily_trades'] = []
        self.data['last_daily_reset_date'] = today
        self.save_data()
```

### 2. ⚠️ CRITICAL: Daily Trades List Never Cleaned Up
**Location:** `real_trading.py` - `execute_arb()` line 554
**Problem:**
- `daily_trades` list grows indefinitely, old entries are never removed
- After many days, the JSON file grows large and memory usage increases
- No automatic cleanup mechanism

**Impact:** Poor performance and disk usage over time
**Severity:** HIGH - Degrades performance but doesn't block trading

**Fix:** Implement daily cleanup in reset logic above

### 3. ⚠️ HIGH: Risk Check Uses Rough Estimate
**Location:** `real_trading.py` line 446
**Problem:**
```python
risk_ok, risk_msg = self._check_risk_controls(amount_per_leg * 2)
```
- Uses `amount_per_leg * 2` as rough estimate for 2 legs
- But actual cost is computed from `risk_detail['totalCost']`
- May reject trades that would actually fit, or accept trades that exceed limits

**Impact:** Risk controls not precise
**Severity:** MEDIUM - May cause false rejections

**Fix:** Calculate actual cost before risk check
```python
total_cost_usd = (risk_detail['totalCost'] / 100.0) * quantity
risk_ok, risk_msg = self._check_risk_controls(total_cost_usd)
```

### 4. ⚠️ HIGH: Market ID Extraction Logic Has Issues
**Location:** `real_trading.py` lines 506-517
**Problem:**
- For away leg with Kalshi: `kalshi.get('away_ticker')` - but might be `away_market_id`
- For home leg with Kalshi: `kalshi.get('home_ticker')` - but might be `home_market_id`
- Inconsistent naming between platforms

**Impact:** Orders may fail due to missing market IDs
**Severity:** HIGH - May cause order placement failures

**Fix:** Check both possible field names
```python
'market_id': (poly.get('away_market_id') or poly.get('market_id')) if away_platform == 'Polymarket' 
            else (kalshi.get('away_ticker') or kalshi.get('away_market_id')),
```

### 5. ⚠️ MEDIUM: Balance Update Order Issue
**Location:** `real_trading.py` lines 550-551
**Problem:**
```python
self.data['bets'].append(trade)
self.data['balance'] -= total_cost_usd
self.save_data()
```
- If `save_data()` fails, balance is deducted but trade not saved
- Inconsistent state between file and memory

**Impact:** Potential balance discrepancy if save fails
**Severity:** MEDIUM - Rare edge case but serious if occurs

**Fix:** Wrap in try-catch with rollback
```python
try:
    self.data['bets'].append(trade)
    self.data['balance'] -= total_cost_usd
    self.save_data()
except Exception as e:
    self.data['bets'].pop()  # Rollback
    self.data['balance'] += total_cost_usd
    raise
```

### 6. ⚠️ MEDIUM: Order Placement Without Quantity Validation
**Location:** `real_trading.py` line 538-547
**Problem:**
- No validation that market_id is actually valid
- No validation that quantity > 0
- No validation that price is within valid range (0-1 for binary options)

**Impact:** May send invalid orders to platforms
**Severity:** MEDIUM - Platforms will reject, but errors propagate

**Fix:** Add validation before placement
```python
if quantity <= 0:
    return False, "Invalid quantity (must be > 0)"
if not (0 < price < 1):
    return False, "Invalid price (must be between 0 and 1)"
if not market_id:
    return False, "Missing market ID"
```

### 7. ⚠️ MEDIUM: Settlement Check Incomplete
**Location:** `real_trading.py` line 686
**Problem:**
```python
if all_legs_resolved and resolved_legs_count == len(bet['legs']):
```
- Only settles if ALL legs resolved
- If one leg resolves and other is still pending, trade stays in "pending" forever
- No timeout mechanism for old pending trades

**Impact:** Stale trades remain in pending status indefinitely
**Severity:** MEDIUM - Doesn't affect trading but causes data clutter

**Fix:** Add timeout mechanism
```python
# If trade is older than 24 hours and not fully resolved, mark as incomplete
if not all_legs_resolved:
    trade_age = datetime.now() - datetime.fromisoformat(bet['timestamp'])
    if trade_age.total_seconds() > 86400:  # 24 hours
        bet['status'] = 'incomplete'
        print(f"Trade {bet['id']} marked as incomplete (timeout)")
```

### 8. ⚠️ LOW: Error Logging Not Bounded During Tests
**Location:** `real_trading.py` line 651
**Problem:**
- Keeps only last 100 errors: `self.data['errors'] = self.data['errors'][-100:]`
- During testing, errors list grows very large first
- No issue in production but wastes memory during development

**Impact:** Minor performance impact during heavy testing
**Severity:** LOW - Not a trading issue

---

## Non-Critical Issues

### 9. Style: Inconsistent Exception Handling
**Location:** Multiple places with bare `except` blocks
**Issue:** Should catch specific exceptions
```python
except Exception as e:  # Too broad
except (requests.Timeout, requests.ConnectionError) as e:  # Better
```

### 10. Style: Missing Type Hints
**Location:** Various method signatures
**Issue:** Some methods could use better type hints for clarity

### 11. Documentation: Missing Docstring Details
**Location:** Trading client methods
**Issue:** Should document expected API response format

---

## Summary

| Priority | Issue | Impact | Fix Time |
|----------|-------|--------|----------|
| CRITICAL | Daily loss never resets | Blocks trading | 10 min |
| CRITICAL | Risk check uses estimate | Inaccurate limits | 5 min |
| HIGH | Market ID extraction | Order failures | 5 min |
| HIGH | Daily trades cleanup | Memory leak | 5 min |
| MEDIUM | Balance update rollback | Data inconsistency | 10 min |
| MEDIUM | Settlement timeout | Data clutter | 10 min |
| MEDIUM | Order validation missing | Invalid orders | 5 min |
| LOW | Logging during tests | Memory | 2 min |

**Total Fix Time: ~50 minutes**

---

## Recommendations

1. **Immediate:** Fix critical issues (daily reset, risk check)
2. **Before Deployment:** Fix all HIGH issues
3. **After Deployment:** Monitor for MEDIUM issues
4. **Future:** Refactor exception handling (LOW priority)
