#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
from datetime import datetime

# =====================================================
# HEADER
# =====================================================
print("╭──────────────────────────────╮")
print("│ INDEX RSI SCANNER (PRO+)    │")
print("│ Market Strength Engine      │")
print("╰──────────────────────────────╯\n")

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")
OUTPUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\rsi")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================
# RSI FUNCTION
# =====================================================
def calculate_rsi(df, period=14):
    delta = df['close'].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

    return df

# =====================================================
# RSI CLASSIFICATION
# =====================================================
def classify_rsi(rsi):
    if rsi < 30:
        return "OVERSOLD"
    elif rsi < 45:
        return "WEAK"
    elif rsi < 60:
        return "NEUTRAL"
    elif rsi < 70:
        return "STRONG"
    else:
        return "OVERBOUGHT"

# =====================================================
# MAIN LOOP
# =====================================================
all_data = []
checked = 0
all_dates = []   # ✅ FIX

files = list(INDEX_DIR.glob("*.csv"))

for file in files:
    try:
        df = pd.read_csv(file)

        if df.empty:
            continue

        df.columns = [c.strip().lower() for c in df.columns]

        df.rename(columns={"trade_date": "date"}, inplace=True)

        if not {'date','close'}.issubset(df.columns):
            continue

        # =====================================================
        # 🔥 DATE FIX
        # =====================================================
        if df["date"].dtype in ["int64", "float64"]:
            df["date"] = pd.to_datetime(df["date"].astype(str), errors='coerce')
        else:
            df["date"] = pd.to_datetime(df["date"], errors='coerce')

        df = df.dropna(subset=['date'])
        df = df[df["date"] > "2000-01-01"]
        df = df.sort_values("date")

        if len(df) < 50:
            continue

        # ✅ collect latest date
        all_dates.append(df["date"].max())

        checked += 1

        df = calculate_rsi(df)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        rsi = latest['rsi']
        prev_rsi = prev['rsi']

        momentum = "RISING" if rsi > prev_rsi else "FALLING"

        all_data.append({
            "Index": file.stem,
            "Date": latest["date"].strftime("%Y-%m-%d"),
            "RSI": round(rsi, 2),
            "Momentum": momentum,
            "Zone": classify_rsi(rsi)
        })

    except:
        continue

# =====================================================
# DATAFRAME
# =====================================================
df_all = pd.DataFrame(all_data)

if df_all.empty:
    print("❌ No data processed")
    exit()

df_all = df_all.sort_values("RSI")

# =====================================================
# FINAL DATE
# =====================================================
if all_dates:
    final_date = max(all_dates).strftime("%Y-%m-%d")
else:
    final_date = datetime.now().strftime("%Y-%m-%d")

# =====================================================
# DISPLAY
# =====================================================
print(f"\n📅 Data Date Used: {final_date}")

print("\n📊 ALL INDEX RSI VALUES")
print(df_all.to_string(index=False))

# =====================================================
# ZONES
# =====================================================
oversold = df_all[df_all["RSI"] < 30]
overbought = df_all[df_all["RSI"] > 70]

print("\n🟢 RSI < 30")
print(oversold if not oversold.empty else "None")

print("\n🔴 RSI > 70")
print(overbought if not overbought.empty else "None")

# =====================================================
# MARKET REGIME
# =====================================================
score = 0

for _, row in df_all.iterrows():
    if row["RSI"] > 60:
        score += 1
    elif row["RSI"] < 40:
        score -= 1

print("\n🧠 MARKET INSIGHT")

if score >= 5:
    print("🚀 STRONG BULLISH MARKET")
elif score <= -5:
    print("🔻 STRONG BEARISH MARKET")
elif len(overbought) >= 3:
    print("⚠ Overbought → Pullback risk")
elif len(oversold) >= 3:
    print("🔥 Oversold → Bounce likely")
else:
    print("⚖ Neutral")

# =====================================================
# SAVE
# =====================================================
timestamp_file = OUTPUT_DIR / f"index_rsi_{final_date}.csv"
latest_file = OUTPUT_DIR / "index_rsi_latest.csv"

df_all.to_csv(timestamp_file, index=False)
df_all.to_csv(latest_file, index=False)

print("\n💾 FILES SAVED")
print(f"→ {timestamp_file}")
print(f"→ {latest_file}")

# =====================================================
# SUMMARY
# =====================================================
print("\n📊 SUMMARY")
print(f"Checked Files: {checked}")
print(f"Oversold: {len(oversold)}")
print(f"Overbought: {len(overbought)}")