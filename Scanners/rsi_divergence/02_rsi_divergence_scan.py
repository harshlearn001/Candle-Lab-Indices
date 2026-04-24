#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

print("╭──────────────────────────────╮")
print("│ INDEX RSI DIVERGENCE        │")
print("│ Reversal Detection Engine   │")
print("╰──────────────────────────────╯\n")

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\rsi")
OUT_DIR.mkdir(parents=True, exist_ok=True)

signals = []
checked = 0
all_dates = []   # ✅ FIX

files = list(INDEX_DIR.glob("*.csv"))

# =====================================================
# RSI FUNCTION
# =====================================================
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    return df

# =====================================================
# SWING DETECTION
# =====================================================
def find_swings(df, window=5):
    df['swing_high'] = df['High'][
        df['High'] == df['High'].rolling(window, center=True).max()
    ]

    df['swing_low'] = df['Low'][
        df['Low'] == df['Low'].rolling(window, center=True).min()
    ]

    return df

# =====================================================
# MAIN LOOP
# =====================================================
for file in files:

    try:
        df = pd.read_csv(file)

        if df.empty:
            continue

        df.columns = [c.strip().capitalize() for c in df.columns]
        df.rename(columns={"Trade_date": "Date"}, inplace=True)

        if not {'Date','Open','High','Low','Close'}.issubset(df.columns):
            continue

        # =====================================================
        # 🔥 DATE FIX
        # =====================================================
        if df["Date"].dtype in ["int64", "float64"]:
            df["Date"] = pd.to_datetime(df["Date"].astype(str), errors="coerce")
        else:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        df = df.dropna(subset=["Date"])
        df = df[df["Date"] > "2000-01-01"]
        df = df.sort_values("Date")

        if len(df) < 60:
            continue

        # ✅ collect latest date
        all_dates.append(df["Date"].max())

        checked += 1

        df = calculate_rsi(df)
        df['EMA50'] = df['Close'].ewm(span=50).mean()
        df = find_swings(df)

        swing_lows = df.dropna(subset=['swing_low'])
        swing_highs = df.dropna(subset=['swing_high'])

        latest = df.iloc[-1]

        # =======================
        # BULLISH DIVERGENCE
        # =======================
        if len(swing_lows) >= 2:

            prev = swing_lows.iloc[-2]
            curr = swing_lows.iloc[-1]

            if (
                curr['Low'] < prev['Low'] and
                curr['RSI'] > prev['RSI'] and
                curr['RSI'] < 45 and
                curr['Close'] > df['EMA50'].iloc[-1]
            ):

                strength = round(curr['RSI'] - prev['RSI'], 2)

                signals.append({
                    "Index": file.stem,
                    "Date": latest["Date"].strftime("%Y-%m-%d"),
                    "Type": "BULLISH",
                    "Close": round(latest['Close'],2),
                    "RSI": round(latest['RSI'],2),
                    "Strength": strength
                })

                print(f"🟢 Bullish → {file.stem}")

        # =======================
        # BEARISH DIVERGENCE
        # =======================
        if len(swing_highs) >= 2:

            prev = swing_highs.iloc[-2]
            curr = swing_highs.iloc[-1]

            if (
                curr['High'] > prev['High'] and
                curr['RSI'] < prev['RSI'] and
                curr['RSI'] > 55 and
                curr['Close'] < df['EMA50'].iloc[-1]
            ):

                strength = round(prev['RSI'] - curr['RSI'], 2)

                signals.append({
                    "Index": file.stem,
                    "Date": latest["Date"].strftime("%Y-%m-%d"),
                    "Type": "BEARISH",
                    "Close": round(latest['Close'],2),
                    "RSI": round(latest['RSI'],2),
                    "Strength": strength
                })

                print(f"🔴 Bearish → {file.stem}")

    except Exception as e:
        print(f"ERROR → {file.stem} | {e}")

# =====================================================
# FINAL DATE
# =====================================================
if all_dates:
    final_date = max(all_dates).strftime("%Y-%m-%d")
else:
    final_date = datetime.now().strftime("%Y-%m-%d")

OUT_FILE = OUT_DIR / f"index_rsi_divergence_{final_date}.csv"

print(f"\n📅 Data Date Used: {final_date}")

# =====================================================
# OUTPUT
# =====================================================
df_out = pd.DataFrame(signals)

print("\n" + "─"*80)
print("📊 INDEX DIVERGENCE SUMMARY")
print("─"*80)
print(f"Checked: {checked}")
print(f"Signals: {len(df_out)}")

if not df_out.empty:

    df_out = df_out.sort_values("Strength", ascending=False)

    print("\n📊 DIVERGENCE SIGNALS")
    print(df_out)

    df_out.to_csv(OUT_FILE, index=False)
    print(f"\n✔ Saved → {OUT_FILE}")

    print("\n🧠 MARKET INSIGHT")

    bull = len(df_out[df_out["Type"]=="BULLISH"])
    bear = len(df_out[df_out["Type"]=="BEARISH"])

    if bull > bear:
        print("🟢 Bullish reversal signals dominant")
    elif bear > bull:
        print("🔴 Bearish reversal signals dominant")
    else:
        print("⚖ Mixed / Neutral divergence")

else:
    print("\n❌ No divergence found")