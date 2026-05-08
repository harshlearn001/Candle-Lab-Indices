#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
from datetime import datetime

print("╭──────────────────────────────╮")
print("│ INDEX BREADTH ENGINE        │")
print("│ Market Participation Engine │")
print("╰──────────────────────────────╯\n")

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\Breadth")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================
# STORAGE
# =====================================================
advances = 0
declines = 0
unchanged = 0
checked = 0
all_dates = []

files = list(INDEX_DIR.glob("*.csv"))

# =====================================================
# MAIN LOOP
# =====================================================
for file in files:

    try:
        df = pd.read_csv(file)

        if df.empty:
            continue

        df.columns = df.columns.str.strip().str.upper()
        df.rename(columns={"TRADE_DATE": "DATE"}, inplace=True)

        if not {"DATE","CLOSE"}.issubset(df.columns):
            continue

        # DATE FIX
        if df["DATE"].dtype in ["int64", "float64"]:
            df["DATE"] = pd.to_datetime(df["DATE"].astype(str), errors="coerce")
        else:
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

        df = df.dropna(subset=["DATE"])
        df = df[df["DATE"] > "2000-01-01"]
        df = df.sort_values("DATE")

        if len(df) < 2:
            continue

        all_dates.append(df["DATE"].max())

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        checked += 1

        if latest["CLOSE"] > prev["CLOSE"]:
            advances += 1
        elif latest["CLOSE"] < prev["CLOSE"]:
            declines += 1
        else:
            unchanged += 1

    except:
        continue

# =====================================================
# FINAL DATE
# =====================================================
if all_dates:
    final_date = max(all_dates).strftime("%Y-%m-%d")
else:
    final_date = datetime.now().strftime("%Y-%m-%d")

OUT_FILE = OUT_DIR / f"index_breadth_{final_date}.csv"

print(f"📅 Data Date Used: {final_date}")

# =====================================================
# CALCULATION
# =====================================================
if declines == 0:
    adr = float('inf')  # extreme bullish
else:
    adr = advances / declines

bullish_pct = (advances / checked * 100) if checked > 0 else 0

# =====================================================
# CLASSIFICATION
# =====================================================
if adr > 2:
    direction = "Bullish"
    strength = "STRONG"
elif adr > 1.2:
    direction = "Bullish"
    strength = "NORMAL"
elif adr < 0.5:
    direction = "Bearish"
    strength = "STRONG"
elif adr < 0.8:
    direction = "Bearish"
    strength = "NORMAL"
else:
    direction = "Neutral"
    strength = "WEAK"

# =====================================================
# OUTPUT
# =====================================================
print("\n📊 SUMMARY")
print(f"Checked   : {checked}")
print(f"Advances  : {advances}")
print(f"Declines  : {declines}")
print(f"ADR       : {round(adr,2) if adr != float('inf') else 'INF'}")
print(f"Bullish % : {round(bullish_pct,2)}%")

print("\n🧠 MARKET INSIGHT")
print(f"{direction} ({strength})")

# =====================================================
# SAVE (MASTER ENGINE READY FORMAT)
# =====================================================
df_out = pd.DataFrame([{
    "Pattern": "Breadth",
    "Direction": direction,
    "Strength": strength,
    "Date": final_date,
    "Checked": checked,
    "Advances": advances,
    "Declines": declines,
    "Bullish_%": round(bullish_pct,2),
    "ADR": round(adr,2) if adr != float('inf') else "INF"
}])

df_out.to_csv(OUT_FILE, index=False)

print(f"\n✔ Saved → {OUT_FILE}")