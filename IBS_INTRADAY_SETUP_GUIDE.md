# IBS Intraday Strategy Setup Guide

## Overview

This guide covers setting up IBS (Internal Bar Strength) to:
1. Calculate on **daily bars** (data2) to identify oversold conditions
2. Execute on **intraday bars** (data1) - 5-minute or 15-minute
3. Use **bracket orders** with limit entry, stop loss, and profit target

---

## Two Approaches Available

### **Approach 1: Portfolio Trader (Partial Solution)** ⚠️

**Files:**
- `Signal Base/IBS_Signal_Base_Intraday.txt`
- `Portfolio MM/IBS_Portfolio_MM_Intraday.txt`

**Capabilities:**
- ✅ Multi-timeframe (daily IBS, intraday execution)
- ✅ Multiple assets simultaneously
- ✅ Portfolio-level position sizing
- ⚠️ **Simulated** stop loss/target (not true bracket orders)
- ❌ Cannot place true limit entry orders
- ❌ Stops/targets checked only at bar close

**Best for:**
- Portfolio rotation across multiple ETFs
- End-of-bar execution acceptable
- Don't need tick-level stop precision

---

### **Approach 2: Regular Strategy (Full Solution)** ✅ RECOMMENDED

**File:**
- `IBS_Intraday_Bracket_Strategy.txt`

**Capabilities:**
- ✅ Multi-timeframe (daily IBS, intraday execution)
- ✅ **TRUE limit entry orders**
- ✅ **TRUE stop loss orders** (executed intra-bar)
- ✅ **TRUE profit target orders** (executed intra-bar)
- ✅ OCO bracket orders (one-cancels-other)
- ✅ Trailing stop option
- ✅ Position sizing based on risk
- ❌ Single asset per strategy instance

**Best for:**
- Single instrument trading (SPY, QQQ)
- Precise stop/target execution
- True bracket order functionality

---

## Setup Instructions

### **APPROACH 1: Portfolio Trader Setup**

#### **Step 1: Chart Configuration**

For each symbol (e.g., SPY, QQQ, IWM):

```
Symbol: SPY
├─ data(1): 15 Minutes
│   ├─ Interval: 15 min
│   ├─ Session: Regular (9:30 AM - 4:00 PM)
│   └─ Type: Regular Close
│
└─ data(2): 1 Day
    ├─ Interval: Daily
    ├─ Type: Regular Close
    └─ Minimum history: 20 days
```

#### **Step 2: Apply Signal Base**

```
Signal: IBS_Signal_Base_Intraday

Inputs:
  IntradayData = 1     (data1 = 15-min bars)
  DailyData = 2        (data2 = daily bars)
  IBSThreshold = 0.2   (oversold below 0.2)
  ATRLength = 14       (14-day ATR)
  StopATRMultiple = 2.0   (stop = 2x ATR)
  TargetATRMultiple = 3.0 (target = 3x ATR)
```

#### **Step 3: Apply Portfolio MM**

```
Portfolio MM: IBS_Portfolio_MM_Intraday

Inputs:
  TopN = 1                 (hold 1 position)
  UseIntradayEntry = True  (wait for pullback)
  UseStopLoss = True       (enable stops)
  UseProfitTarget = True   (enable targets)
  VerboseMode = True       (see details)
```

#### **Step 4: Run in Portfolio Trader**

- Portfolio Backtester or Portfolio Trader mode
- Will manage entries/exits across multiple symbols
- Rebalances every bar (intraday)

---

### **APPROACH 2: Regular Strategy Setup** (RECOMMENDED)

#### **Step 1: Chart Configuration**

Single symbol chart (e.g., SPY only):

```
Symbol: SPY
├─ data(1): 15 Minutes
│   ├─ Interval: 15 min
│   ├─ Session: Regular (9:30 AM - 4:00 PM)
│   └─ Type: Regular Close
│
└─ data(2): 1 Day
    ├─ Interval: Daily
    ├─ Type: Regular Close
    └─ Minimum history: 20 days
```

#### **Step 2: Apply Strategy**

```
Strategy: IBS_Intraday_Bracket

Inputs:
  // IBS Parameters
  IBSThreshold = 0.2
  IBSExitLevel = 0.8

  // Entry
  UseLimit = True
  LimitOffsetPercent = 0.2  (enter 0.2% below close)

  // Risk Management
  ATRLength = 14
  StopATRMultiple = 2.0     (stop 2 ATR below entry)
  TargetATRMultiple = 3.0   (target 3 ATR above entry)
  UseTrailingStop = False
  TrailATRMultiple = 1.5

  // Time Filters
  StartTime = 0930
  EndTime = 1545            (no entries after 3:45 PM)
  ExitEOD = True            (close all at 3:55 PM)

  // Position Sizing
  RiskPercent = 1.0         (risk 1% per trade)

  // Display
  VerboseMode = True
```

#### **Step 3: Strategy Properties**

**CRITICAL - Set these in Strategy Properties:**

```
Format Strategy > Properties:

Costs:
  ☑ Commission: $1.00 per side (adjust for your broker)
  ☑ Slippage: 1 tick

Trade Size:
  ☐ Use default contracts
  ☑ Use strategy calculation (uses RiskPercent sizing)

Broker Emulator:
  ☑ Enable intrabar order generation
  ☑ IOG: On every tick (for precise stops)
```

**Without "Intrabar Order Generation", stops/targets won't work properly!**

---

## How It Works

### **Signal Generation (Daily Bars - data2)**

```
Day 1 End:
  SPY Daily:
    High: $500.00
    Low:  $495.00
    Close: $495.50

  IBS = (495.50 - 495.00) / (500.00 - 495.00)
      = 0.50 / 5.00
      = 0.10  ← OVERSOLD (< 0.2 threshold)

  ATR(14) = $3.00

  Signal Generated:
    Entry Limit = $495.50 * (1 - 0.002)
                = $494.50
    Stop Loss = $494.50 - ($3.00 * 2.0)
              = $488.50
    Target = $494.50 + ($3.00 * 3.0)
           = $503.50
```

### **Execution (Intraday Bars - data1)**

```
Day 2, 10:00 AM (15-min bar):
  SPY intraday: $496.00
  Entry Limit: $494.50
  Action: Wait (price above limit)

Day 2, 10:15 AM:
  SPY intraday: $494.20 (dips to limit)
  Action: BUY at $494.50 limit
  → Limit order fills at $494.50

  Bracket orders activate:
    Stop Loss: $488.50
    Profit Target: $503.50

Day 2, 11:30 AM:
  SPY rallies to $503.60
  Action: Profit Target HIT!
  → SELL at $503.50

  Profit: $503.50 - $494.50 = $9.00 per share
        = +1.82%
```

---

## Order Flow Diagram

**Approach 2 (Regular Strategy) - TRUE Bracket Orders:**

```
Daily Bar Closes → IBS < 0.2 Detected
         ↓
Next Intraday Bar Opens
         ↓
PLACE LIMIT BUY ORDER at $494.50
         ↓
    ┌────────────────────┐
    │  Waiting for Fill  │
    └────────────────────┘
         ↓
    Order Fills at $494.50
         ↓
    ┌──────────────────────────────────┐
    │  BRACKET ORDERS ACTIVATE (OCO)   │
    ├──────────────────────────────────┤
    │  ├─ Stop Loss: $488.50           │
    │  └─ Profit Target: $503.50       │
    └──────────────────────────────────┘
         ↓
    ┌─────────────────────────┐
    │  One of these triggers: │
    ├─────────────────────────┤
    │  A) Stop Hit → Exit     │
    │  B) Target Hit → Exit   │
    │  C) EOD → Exit at 3:55  │
    │  D) IBS > 0.8 → Exit    │
    └─────────────────────────┘
```

---

## Key Differences: Approach 1 vs 2

| Feature | Portfolio Trader (Approach 1) | Regular Strategy (Approach 2) |
|---------|-------------------------------|-------------------------------|
| **Entry Order** | Market only (next bar) | TRUE Limit order ✅ |
| **Stop Loss** | Checked at bar close ⚠️ | Intrabar execution ✅ |
| **Profit Target** | Checked at bar close ⚠️ | Intrabar execution ✅ |
| **Multiple Assets** | Yes (10+ symbols) ✅ | One per instance ⚠️ |
| **OCO Orders** | No ❌ | Yes ✅ |
| **Trailing Stop** | No ❌ | Yes ✅ |
| **Position Sizing** | % of portfolio | Risk-based ✅ |
| **Execution Precision** | End of bar | Tick-by-tick ✅ |

---

## Expected Performance

### **Backtesting SPY (15-min bars)**

**Typical statistics (will vary):**

```
Total Trades: 40-60 per year
Win Rate: 55-65%
Avg Win: +1.5% to +2.5%
Avg Loss: -0.8% to -1.2%
Risk/Reward: 1:1.5 to 1:2.0
Annual Return: 8-15% (before costs)
Max Drawdown: 8-12%
Sharpe Ratio: 0.8-1.2
```

**Transaction costs impact:**
- Spread: ~$0.01 = 0.002% per side
- Commission: ~$1.00 per side
- Slippage: ~$0.02 on limit fills
- **Total round-trip: ~0.01-0.02%**
- With 50 trades/year: **0.5-1.0% annual drag**

---

## Common Issues & Solutions

### **Issue 1: Stops Not Executing Mid-Bar**

**Problem:** Stop loss should trigger at $488.50, but price goes to $487.00 and comes back, stop never triggers.

**Solution:**
- ✅ Enable "Intrabar Order Generation" in Strategy Properties
- ✅ Set IOG to "On every tick" (not "On price change")
- ❌ Don't use Portfolio Trader for this (can't do intrabar)

### **Issue 2: Limit Orders Never Fill**

**Problem:** Entry limit at $494.50, price goes to $494.60 but doesn't fill.

**Solution:**
- Price must touch or cross the limit
- Check data quality (missing ticks?)
- Use `SetStopContract` instead of limit if unreliable

### **Issue 3: Too Many Trades (Overtrading)**

**Problem:** 200+ trades per year, costs eating profits.

**Solution:**
- Increase IBSThreshold (e.g., 0.15 instead of 0.20)
- Add time filter (only trade first 2 hours)
- Use daily entries, not intraday

### **Issue 4: Portfolio Trader Stops Don't Work**

**Problem:** Stop should exit at $488.50, but holds to $485.00.

**Solution:**
- **This is expected** - Portfolio Trader checks only at bar close
- Switch to Approach 2 (Regular Strategy) for true stops
- Or accept bar-close exits only

---

## Optimization Tips

### **1. IBS Threshold**

```
Test range: 0.10 to 0.30
Optimal: Usually 0.15-0.25

Too low (0.05): Too few trades
Too high (0.40): Enters too early (not oversold)
```

### **2. ATR Multiples**

```
Stop Loss: 1.5 to 3.0 ATR
  Lower = tighter stop, more losses
  Higher = wider stop, better win rate

Profit Target: 2.0 to 5.0 ATR
  Lower = more wins, smaller profits
  Higher = fewer wins, larger profits

Optimal R:R = 1:1.5 to 1:2.5
```

### **3. Time Filters**

```
Best entry times (SPY):
  9:30-10:00 AM: High volatility, good fills
  10:00-11:00 AM: Pullback entries common
  2:00-3:00 PM: Late-day reversals

Avoid:
  3:45-4:00 PM: Too close to close
  First 5 minutes: Wide spreads
```

### **4. Position Sizing**

```
Conservative: 0.5% risk per trade
Moderate: 1.0% risk per trade
Aggressive: 2.0% risk per trade

Never exceed 2% risk on a single trade!
```

---

## Testing Checklist

Before going live:

- [ ] Backtest on 2+ years of data
- [ ] Forward test (out-of-sample) 6+ months
- [ ] Paper trade 1 month minimum
- [ ] Verify IOG is enabled (Approach 2)
- [ ] Check commission/slippage settings
- [ ] Confirm stops trigger intrabar
- [ ] Test with small position size first
- [ ] Monitor first 10 trades closely
- [ ] Track actual vs expected performance

---

## Recommended Setup

**For single-instrument trading (SPY):**
→ Use **Approach 2** (Regular Strategy)
- TRUE bracket orders
- Intrabar stop execution
- Better risk management

**For multi-instrument rotation (10 ETFs):**
→ Use **Approach 1** (Portfolio Trader)
- Manage multiple positions
- Accept bar-close exits
- Simpler than running 10 strategy instances

---

## Files Summary

```
Created Files:
├── Signal Base/IBS_Signal_Base_Intraday.txt
│   └── Calculates IBS on data(2) daily, sends to PMM
│
├── Portfolio MM/IBS_Portfolio_MM_Intraday.txt
│   └── Manages entries/exits for Portfolio Trader
│
├── IBS_Intraday_Bracket_Strategy.txt
│   └── Full bracket order strategy (RECOMMENDED)
│
└── IBS_INTRADAY_SETUP_GUIDE.md (this file)
    └── Complete setup instructions
```

---

## Questions?

**Q: Can I use 5-minute bars instead of 15-minute?**
A: Yes, just set data(1) to 5-minute interval. More signals, higher costs.

**Q: Does this work on stocks or just ETFs?**
A: Works on any liquid instrument. Best on SPY/QQQ. Avoid low-volume stocks.

**Q: Can I short using IBS > 0.8?**
A: Yes, but IBS works better long (buying oversold) than short (selling overbought).

**Q: What about crypto or futures?**
A: Crypto: Yes (24hr markets, may need time filter)
   Futures: Yes (adjust ATR for contract size)

**Q: Why not just use daily bars for everything?**
A: Daily works fine! Intraday gives more precise entries but adds complexity.

---

## Final Recommendation

**Start Simple:**
1. Use **Approach 2** (Regular Strategy)
2. Trade **SPY only** on **15-minute bars**
3. Use **daily IBS** (data2)
4. Default parameters (0.2 threshold, 2.0/3.0 ATR)
5. Paper trade 20 trades
6. If successful, go live with small size
7. Only then optimize or add complexity

**Good luck!**
