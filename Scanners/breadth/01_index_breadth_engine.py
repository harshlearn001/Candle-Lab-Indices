#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CANDLE-LAB | INDEX BREADTH ENGINE

✔ Data-driven date (no system date)
✔ Robust date parsing (fixes 1970 issue)
✔ Advance / Decline calculation
✔ Market insight output
✔ Clean CSV save
"""

from pathlib import Path
import pandas as pd
from datetime import datetime

# =====================================================
# HEADER
# =====================================================
print("╭──────────────────────────────╮")
print("│ INDEX BREADTH ENGINE        │")
print("│ Market Participation Engine │")
print("╰──────────────────────────────╯\n")

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\breadth")
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

        # =====================================================
        # DATE FIX (CRITICAL)
        # =====================================================
        if df["DATE"].dtype in ["int64", "float64"]:
            df["DATE"] = pd.to_datetime(df["DATE"].astype(str), errors="coerce")
        else:
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

        df = df.dropna(subset=["DATE"])

        # Remove bad dates (1970 issue)
        df = df[df["DATE"] > "2000-01-01"]

        df = df.sort_values("DATE")

        if len(df) < 2:
            continue

        # Collect latest valid date
        all_dates.append(df["DATE"].max())

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        checked += 1

        # =====================================================
        # ADVANCE / DECLINE
        # =====================================================
        if latest["CLOSE"] > prev["CLOSE"]:
            advances += 1
        elif latest["CLOSE"] < prev["CLOSE"]:
            declines += 1
        else:
            unchanged += 1

    except Exception as e:
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
adr = advances / declines if declines != 0 else 0
bullish_pct = (advances / checked * 100) if checked > 0 else 0

# =====================================================
# OUTPUT
# =====================================================
print("────────────────────────────────────────")
print("📊 INDEX BREADTH SUMMARY")
print("────────────────────────────────────────")

print(f"Indices Checked : {checked}")
print(f"Advances        : {advances}")
print(f"Declines        : {declines}")
print(f"Unchanged       : {unchanged}")
print(f"ADR             : {round(adr,2)}")
print(f"Bullish %       : {round(bullish_pct,2)}%")

# =====================================================
# INTERPRETATION
# =====================================================
print("\n🧠 MARKET INSIGHT")

if adr > 2:
    insight = "🔥 Strong Bullish Breadth"
elif adr > 1.2:
    insight = "🟢 Bullish Breadth"
elif adr < 0.5:
    insight = "💀 Strong Bearish Breadth"
elif adr < 0.8:
    insight = "🔴 Bearish Breadth"
else:
    insight = "⚖ Neutral Breadth"

print(insight)

# =====================================================
# SAVE
# =====================================================
df_out = pd.DataFrame([{
    "Date": final_date,
    "Checked": checked,
    "Advances": advances,
    "Declines": declines,
    "Unchanged": unchanged,
    "ADR": round(adr,2),
    "Bullish_%": round(bullish_pct,2),
    "Insight": insight
}])

df_out.to_csv(OUT_FILE, index=False)

print(f"\n✔ Saved → {OUT_FILE}")