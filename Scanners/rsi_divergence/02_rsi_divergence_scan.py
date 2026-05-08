#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
from datetime import datetime

print("╭──────────────────────────────╮")
print("│ INDEX RSI DIVERGENCE        │")
print("│ Reversal Detection Engine   │")
print("╰──────────────────────────────╯\n")

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")
OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\RSI_Divergence")
OUT_DIR.mkdir(parents=True, exist_ok=True)

signals = []
checked = 0
all_dates = []

files = list(INDEX_DIR.glob("*.csv"))

# =====================================================
# RSI (WILDER)
# =====================================================
def calculate_rsi(df, period=14):
    delta = df['CLOSE'].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    return df

# =====================================================
# SWING DETECTION
# =====================================================
def find_swings(df, window=5):
    df['SWING_HIGH'] = df['HIGH'][
        df['HIGH'] == df['HIGH'].rolling(window, center=True).max()
    ]

    df['SWING_LOW'] = df['LOW'][
        df['LOW'] == df['LOW'].rolling(window, center=True).min()
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

        df.columns = [c.strip().upper() for c in df.columns]
        df.rename(columns={"TRADE_DATE": "DATE"}, inplace=True)

        if not {'DATE','OPEN','HIGH','LOW','CLOSE'}.issubset(df.columns):
            continue

        # DATE FIX
        if df["DATE"].dtype in ["int64", "float64"]:
            df["DATE"] = pd.to_datetime(df["DATE"].astype(str), errors="coerce")
        else:
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

        df = df.dropna(subset=["DATE"])
        df = df[df["DATE"] > "2000-01-01"]
        df = df.sort_values("DATE")

        if len(df) < 60:
            continue

        all_dates.append(df["DATE"].max())
        checked += 1

        df = calculate_rsi(df)
        df['EMA50'] = df['CLOSE'].ewm(span=50).mean()
        df = find_swings(df)

        swing_lows = df.dropna(subset=['SWING_LOW'])
        swing_highs = df.dropna(subset=['SWING_HIGH'])

        latest = df.iloc[-1]

        # =======================
        # BULLISH DIVERGENCE
        # =======================
        if len(swing_lows) >= 2:

            prev = swing_lows.iloc[-2]
            curr = swing_lows.iloc[-1]

            if (
                curr['LOW'] < prev['LOW'] and
                curr['RSI'] > prev['RSI'] and
                curr['RSI'] < 45 and
                curr['CLOSE'] > df['EMA50'].iloc[-1]
            ):

                strength = round(curr['RSI'] - prev['RSI'], 2)

                signals.append({
                    "Index": file.stem,
                    "Pattern": "RSI_Divergence",
                    "Direction": "Bullish",
                    "Date": latest["DATE"].strftime("%Y-%m-%d"),
                    "Close": round(latest['CLOSE'],2),
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
                curr['HIGH'] > prev['HIGH'] and
                curr['RSI'] < prev['RSI'] and
                curr['RSI'] > 55 and
                curr['CLOSE'] < df['EMA50'].iloc[-1]
            ):

                strength = round(prev['RSI'] - curr['RSI'], 2)

                signals.append({
                    "Index": file.stem,
                    "Pattern": "RSI_Divergence",
                    "Direction": "Bearish",
                    "Date": latest["DATE"].strftime("%Y-%m-%d"),
                    "Close": round(latest['CLOSE'],2),
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
# ALWAYS SAVE
# =====================================================
df_out = pd.DataFrame(signals)

if df_out.empty:
    df_out = pd.DataFrame({
        "Message": ["No RSI Divergence"],
        "Date": [final_date]
    })
else:
    df_out = df_out.sort_values("Strength", ascending=False)
    print(df_out)

df_out.to_csv(OUT_FILE, index=False)

print(f"\n✔ Saved → {OUT_FILE}")