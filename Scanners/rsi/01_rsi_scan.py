#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
from datetime import datetime

print("╭──────────────────────────────╮")
print("│ INDEX RSI SCANNER (PRO+)    │")
print("│ Market Strength Engine      │")
print("╰──────────────────────────────╯\n")

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")
OUTPUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\RSI")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================
# RSI (WILDER METHOD)
# =====================================================
def calculate_rsi(df, period=14):
    delta = df['close'].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

    return df

# =====================================================
# CLASSIFICATION
# =====================================================
def classify_rsi(rsi):
    if rsi < 30:
        return "OVERSOLD", "Bullish"
    elif rsi < 45:
        return "WEAK", "Bearish"
    elif rsi < 60:
        return "NEUTRAL", "Neutral"
    elif rsi < 70:
        return "STRONG", "Bullish"
    else:
        return "OVERBOUGHT", "Bearish"

# =====================================================
# MAIN LOOP
# =====================================================
all_data = []
checked = 0
all_dates = []

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

        # DATE FIX
        if df["date"].dtype in ["int64", "float64"]:
            df["date"] = pd.to_datetime(df["date"].astype(str), errors='coerce')
        else:
            df["date"] = pd.to_datetime(df["date"], errors='coerce')

        df = df.dropna(subset=['date'])
        df = df[df["date"] > "2000-01-01"]
        df = df.sort_values("date")

        if len(df) < 50:
            continue

        all_dates.append(df["date"].max())
        checked += 1

        df = calculate_rsi(df)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        rsi = latest['rsi']
        prev_rsi = prev['rsi']

        momentum = "RISING" if rsi > prev_rsi else "FALLING"

        zone, direction = classify_rsi(rsi)

        all_data.append({
            "Index": file.stem,
            "Pattern": "RSI",
            "Direction": direction,
            "Date": latest["date"].strftime("%Y-%m-%d"),
            "RSI": round(rsi, 2),
            "Momentum": momentum,
            "Zone": zone
        })

    except Exception as e:
        print(f"Error in {file.name}: {e}")
        continue

# =====================================================
# DATAFRAME
# =====================================================
df_all = pd.DataFrame(all_data)

# =====================================================
# FINAL DATE
# =====================================================
if all_dates:
    final_date = max(all_dates).strftime("%Y-%m-%d")
else:
    final_date = datetime.now().strftime("%Y-%m-%d")

# =====================================================
# ALWAYS SAVE
# =====================================================
if df_all.empty:
    df_all = pd.DataFrame({
        "Message": ["No RSI Data"],
        "Date": [final_date]
    })
else:
    df_all = df_all.sort_values("RSI")

# =====================================================
# MARKET SCORE
# =====================================================
score = 0

for _, row in df_all.iterrows():
    if row.get("RSI", 50) > 60:
        score += 1
    elif row.get("RSI", 50) < 40:
        score -= 1

# =====================================================
# OUTPUT
# =====================================================
timestamp_file = OUTPUT_DIR / f"index_rsi_{final_date}.csv"
latest_file = OUTPUT_DIR / "index_rsi_latest.csv"

df_all.to_csv(timestamp_file, index=False)
df_all.to_csv(latest_file, index=False)

print(f"\n📅 Data Date Used: {final_date}")
print(f"\n✔ Saved → {timestamp_file}")

# =====================================================
# MARKET INSIGHT
# =====================================================
print("\n🧠 MARKET INSIGHT")

if score >= 5:
    print("🚀 STRONG BULLISH MARKET")
elif score <= -5:
    print("🔻 STRONG BEARISH MARKET")
else:
    print("⚖ NEUTRAL / MIXED")