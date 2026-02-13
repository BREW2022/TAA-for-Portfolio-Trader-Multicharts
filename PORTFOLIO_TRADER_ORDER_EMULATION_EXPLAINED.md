# Portfolio Trader Price Order Emulation - What Works & What Doesn't

## Your Question Was Correct!

You asked: *"the portfolio trader has price order emulation which i think would allow emulating the buy, stop, and target limit order without a bracket. check?"*

**Answer: YES and NO** - it depends on what you mean by "emulation"

---

## What MultiCharts Order Emulation Actually Is

### **For AUTO TRADING (Live/Paper Trading):**

✅ **Full price order emulation available**
- Monitors bid/ask or trade prices in real-time
- When limit/stop price is hit, sends market order to broker
- Works intrabar (tick-by-tick monitoring)
- See: [Auto Trading Documentation](https://www.multicharts.com/trading-software/index.php?title=Auto_Trading)

**Configuration:**
```
Tools > Options > Orders
├─ Stop Orders: Emulate locally using Bid/Ask
├─ Limit Orders: Emulate locally using Trade
└─ Stop-Limit Orders: Emulate locally using Bid/Ask
```

### **For PORTFOLIO BACKTESTER (Historical Testing):**

⚠️ **LIMITED emulation** - Assumptions-based, not tick-by-tick
- Uses OHLC prices of each bar (no tick data)
- Makes assumptions about when limit/stop would fill
- Bar Magnifier NOT available in Portfolio Trader
- See: [Limit Order Execution Assumptions](https://www.multicharts.com/trading-software/index.php?title=Limit_Order_Execution_Assumptions_for_Portfolio_Backtesting)

**Execution assumptions:**
```
Limit Buy Order at $100:
  If Low of bar <= $100:
    Assumed filled at $100 (or better if Open < $100)
  Else:
    Order remains pending

Stop Sell Order at $95:
  If Low of bar <= $95:
    Assumed filled at $95 (or worse if gap down)
  Else:
    Order remains pending
```

---

## Critical Limitation: IOG Not Supported

From [MultiCharts forum discussion](https://www.multicharts.com/discussion/viewtopic.php?t=49980):

> **"IOG is not supported in Portfolio Trader yet"**

**What this means:**

❌ **Intrabar Order Generation (IOG) does NOT work**
- Orders are evaluated only at **bar close**
- Stop loss won't trigger mid-bar even if price hits it
- Profit target won't trigger mid-bar even if price hits it
- No tick-by-tick execution (even in backtesting with tick data)

✅ **But you CAN still use limit/stop orders:**
- They execute based on bar OHLC
- Backtester makes assumptions about fills
- Live trading uses price emulation (monitors ticks)

---

## What You CAN Do in Signal Base

### **YES - EasyLanguage Order Commands Work:**

```easylanguage
// In Signal Base script:

// Entry orders:
buy next bar at 100 limit;           // ✅ Works
buy next bar at market;               // ✅ Works
buy this bar at close;                // ✅ Works

// Exit orders:
sell next bar at 95 stop;             // ✅ Works (but bar-close execution)
sell next bar at 110 limit;           // ✅ Works (profit target)
sell this bar at close;               // ✅ Works

// Advanced:
buy next bar at (Close * 1.02) limit; // ✅ Works (dynamic calculation)
```

### **NO - These Don't Work:**

```easylanguage
// Bracket orders (OC strategy-level):
SetStopLoss(95);                      // ❌ Not in Portfolio Trader Signal
SetProfitTarget(110);                 // ❌ Not in Portfolio Trader Signal

// IOG-dependent:
buy next bar at 100 limit intrabar;   // ❌ IOG not supported
```

---

## How Your Revised Approach Works

### **Architecture:**

```
data(2) Daily Bars
      ↓
  Calculate IBS
      ↓
  IBS < 0.2? → SIGNAL
      ↓
      ├─ Entry: buy next bar at $494.50 limit
      ├─ Stop:  sell next bar at $488.50 stop
      └─ Target: sell next bar at $503.50 limit
      ↓
Portfolio MM
      ↓
  Rank assets by IBS
  Allow entries for Top N
  Set position size
      ↓
data(1) Intraday Bars (15-min)
      ↓
  Orders execute at bar close
```

### **Created Files:**

1. **`Signal Base/IBS_Signal_Base_Intraday_v2.txt`**
   - Calculates IBS on daily (data2)
   - Places limit/stop/target orders directly
   - Orders execute on intraday bars (data1)

2. **`Portfolio MM/IBS_Portfolio_MM_Simple.txt`**
   - Ranks assets by IBS
   - Allows entries for Top N
   - Sets position sizing
   - **Does NOT manage orders** (Signal Base does that)

---

## Execution Example

### **Day 1 EOD - Daily Bar (data2):**

```
SPY Daily:
  High: $500.00
  Low:  $495.00
  Close: $495.50

IBS = 0.10 → OVERSOLD SIGNAL

Signal Base generates:
  Entry:  buy next bar at $494.50 limit
  Stop:   sell next bar at $488.50 stop
  Target: sell next bar at $503.50 limit
```

### **Day 2, 10:00-10:15 AM - 15-min Bar (data1):**

```
Bar OHLC:
  Open: $496.00
  High: $496.50
  Low: $494.20
  Close: $495.00

Execution logic:
  ✅ Low ($494.20) touched limit ($494.50)
  → Assumed filled at $494.50 (or better)

  ❌ High ($496.50) did NOT reach target ($503.50)
  → Target order still pending

  ❌ Low ($494.20) did NOT reach stop ($488.50)
  → Stop order still pending
```

### **Day 2, 11:30-11:45 AM - 15-min Bar:**

```
Bar OHLC:
  Open: $502.00
  High: $503.80
  Low: $501.50
  Close: $503.60

Execution logic:
  ✅ High ($503.80) touched target ($503.50)
  → Profit target FILLS at $503.50
  → Stop order cancelled (position closed)

Profit: $503.50 - $494.50 = $9.00 per share (+1.82%)
```

---

## Key Differences: v1 vs v2 vs Regular Strategy

| Feature | v1 (PMM Managed) | v2 (Signal Base Orders) | Regular Strategy |
|---------|------------------|-------------------------|------------------|
| **Order placement** | In Portfolio MM | In Signal Base ✅ | In Strategy ✅ |
| **Limit entry** | Simulated | Native EasyLanguage ✅ | Native EasyLanguage ✅ |
| **Stop loss** | PMM checks at bar close | EasyLanguage stop order ✅ | SetStopLoss() ✅ |
| **Profit target** | PMM checks at bar close | EasyLanguage limit order ✅ | SetProfitTarget() ✅ |
| **Intrabar execution** | ❌ No | ❌ No (IOG not supported) | ✅ Yes (with IOG) |
| **Code simplicity** | Complex (PMM logic) | Simpler ✅ | Simplest ✅ |
| **Portfolio Trader** | ✅ Yes | ✅ Yes | ❌ No (single instrument) |
| **Multiple assets** | ✅ Yes | ✅ Yes | ⚠️ Need multiple instances |

---

## Live Trading vs Backtesting

### **BACKTESTING (Portfolio Backtester):**

Executes based on OHLC assumptions:

```easylanguage
buy next bar at 100 limit;

// MultiCharts assumes:
If Low <= 100 then
    Fill at 100 (or better if gap down)
Else
    Order pending
```

**Limitations:**
- No tick data (even if you have it)
- No intrabar execution
- Optimistic fill assumptions
- May not reflect real slippage

### **LIVE/PAPER TRADING (Auto Trading):**

Uses actual price emulation:

```easylanguage
buy next bar at 100 limit;

// MultiCharts:
1. Monitors bid/ask prices tick-by-tick
2. When Ask <= 100, sends market buy to broker
3. Actual fill depends on liquidity/slippage
```

**Advantages:**
- Real-time price monitoring
- Actual broker fills
- Realistic slippage
- True emulation

---

## Recommendations

### **For Your Use Case (IBS Intraday):**

**Use v2 approach** (`IBS_Signal_Base_Intraday_v2.txt` + `IBS_Portfolio_MM_Simple.txt`)

**Why:**
1. ✅ Simpler than v1 (orders in Signal Base, not PMM)
2. ✅ Uses native EasyLanguage orders (cleaner code)
3. ✅ Works with multiple assets (Portfolio Trader)
4. ✅ Price emulation in live trading
5. ⚠️ Accept bar-close execution (no IOG anyway)

**Setup:**
```
Chart:
├─ data(1): 15 Minutes (execution)
└─ data(2): 1 Day (IBS signal)

Apply to each symbol:
├─ Signal: IBS_Signal_Base_Intraday_v2
└─ Portfolio MM: IBS_Portfolio_MM_Simple (once for all)
```

### **For Single-Instrument Trading:**

**Use regular strategy** (`IBS_Intraday_Bracket_Strategy.txt`)

**Why:**
1. ✅ TRUE intrabar execution (with IOG enabled)
2. ✅ Stops trigger mid-bar if hit
3. ✅ Cleaner bracket order syntax
4. ✅ Better for precise risk management
5. ❌ Can't do multiple assets easily

---

## Testing Checklist

### **Before Going Live:**

- [ ] Backtest on 6+ months of data
- [ ] Understand that backtest fills are ASSUMPTIONS
- [ ] Paper trade 20+ trades to see REAL fills
- [ ] Compare: Backtest fills vs Paper trade fills
- [ ] Check slippage on limit orders (may not fill at exact price)
- [ ] Verify stop orders fill at or worse than stop price
- [ ] Monitor first 5 live trades very closely
- [ ] Accept that bar-close execution may miss some stops/targets

### **Auto Trading Settings:**

```
Tools > Options > Orders:
├─ ✅ Emulate Stop Orders: Bid/Ask
├─ ✅ Emulate Limit Orders: Trade
└─ ✅ Emulate Stop-Limit Orders: Bid/Ask

Strategy Properties > Properties:
├─ ✅ Enable commission ($1.00 per side)
├─ ✅ Enable slippage (1 tick)
└─ ⚠️ Note: IOG checkbox grayed out (not available)
```

---

## Bottom Line

**Your intuition was correct!** You CAN use limit/stop/target orders in Portfolio Trader Signal Base without needing my complex Portfolio MM logic.

**The trade-off:**
- ✅ Orders work and will execute
- ✅ Price emulation in live trading
- ✅ Simpler code architecture
- ❌ No intrabar execution (IOG limitation)
- ⚠️ Backtest fills are optimistic assumptions

**This is actually BETTER than my original v1 approach** because:
1. Code is simpler and clearer
2. Uses native EasyLanguage orders
3. Leverages Portfolio Trader's built-in order management
4. You correctly identified the capability I missed!

---

## Sources

- [MultiCharts Auto Trading Documentation](https://www.multicharts.com/trading-software/index.php?title=Auto_Trading)
- [Portfolio Backtester Limit Order Assumptions](https://www.multicharts.com/trading-software/index.php?title=Limit_Order_Execution_Assumptions_for_Portfolio_Backtesting)
- [MultiCharts Forum: IOG Not Supported in Portfolio Trader](https://www.multicharts.com/discussion/viewtopic.php?t=49980)
- [Portfolio Trader Manual (PDF)](https://www.multicharts.com/trading-software/images/1/16/Portfolio_Trader_Manual.pdf)
- [Portfolio Trader Strategy Examples](https://www.multicharts.com/trading-software/index.php?title=Portfolio_Trader_Strategy_Examples)

---

## Questions?

**Q: Will my stop loss trigger if price gaps through it?**
A: In backtesting, yes (assumes fill at stop or worse). In live trading, depends on liquidity and gap size.

**Q: Why not just use regular strategy with IOG?**
A: You should! But if you need multi-asset rotation, Portfolio Trader is the only option.

**Q: Can I improve execution with smaller bar intervals (5-min instead of 15-min)?**
A: Yes, smaller bars = more frequent checks for fills. But still no true intrabar execution.

**Q: What about using 1-minute bars?**
A: Works, but very computationally intensive and more transactions costs. Doesn't solve IOG limitation.

Good catch on this feature! Your v2 approach is cleaner.
