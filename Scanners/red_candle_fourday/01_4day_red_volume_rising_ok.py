#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
from datetime import datetime

print("╭──────────────────────────────╮")
print("│ INDEX 4 RED CANDLES         │")
print("│ Rising Selling Pressure     │")
print("╰──────────────────────────────╯\n")

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

# ✅ FIXED NAME
OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\Red_Volume")
OUT_DIR.mkdir(parents=True, exist_ok=True)

results = []
all_dates = []

files = list(INDEX_DIR.glob("*.csv"))

# =====================================================
# PROCESS
# =====================================================
for file in files:

    try:
        df = pd.read_csv(file)

        if df.empty:
            continue

        df.columns = df.columns.str.strip().str.upper()
        df.rename(columns={"TRADE_DATE": "DATE"}, inplace=True)

        if not {"DATE","OPEN","HIGH","LOW","CLOSE"}.issubset(df.columns):
            continue

        # DATE FIX
        if df["DATE"].dtype in ["int64", "float64"]:
            df["DATE"] = pd.to_datetime(df["DATE"].astype(str), errors="coerce")
        else:
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

        df = df.dropna(subset=["DATE"])
        df = df[df["DATE"] > "2000-01-01"]
        df = df.sort_values("DATE")

        if len(df) < 4:
            continue

        all_dates.append(df["DATE"].max())

        last4 = df.tail(4)

        # =====================================================
        # 4 RED CANDLES
        # =====================================================
        red = (last4["CLOSE"] < last4["OPEN"]).all()

        # =====================================================
        # RANGE EXPANSION
        # =====================================================
        ranges = (last4["HIGH"] - last4["LOW"]).values

        if ranges[0] == 0:
            continue

        rising_pressure = (ranges[0] < ranges[1] < ranges[2] < ranges[3])

        if red and rising_pressure:

            range_growth = ranges[3] / ranges[0]
            strength = "STRONG" if range_growth > 2 else "NORMAL"

            results.append({
                "Index": file.stem,
                "Pattern": "4RedExpansion",
                "Direction": "Bearish",
                "Date": last4.iloc[-1]["DATE"].strftime("%Y-%m-%d"),
                "Close": round(last4.iloc[-1]["CLOSE"], 2),
                "RangeGrowth": round(range_growth, 2),
                "Strength": strength
            })

            print(f"{file.stem} → 🔻 BREAKDOWN PRESSURE")

    except Exception as e:
        print(f"Error in {file.name}: {e}")
        continue

# =====================================================
# FINAL DATE
# =====================================================
if all_dates:
    final_date = max(all_dates).strftime("%Y-%m-%d")
else:
    final_date = datetime.now().strftime("%Y-%m-%d")

OUT_FILE = OUT_DIR / f"index_4day_red_{final_date}.csv"

print(f"\n📅 Data Date Used: {final_date}")

# =====================================================
# OUTPUT
# =====================================================
df_out = pd.DataFrame(results)

print("\n📊 SUMMARY")
print(f"Signals Found: {len(df_out)}")

# ALWAYS SAVE
if df_out.empty:
    df_out = pd.DataFrame({
        "Message": ["No Breakdown Pressure Found"],
        "Date": [final_date]
    })
else:
    df_out = df_out.sort_values("RangeGrowth", ascending=False)
    print(df_out)

df_out.to_csv(OUT_FILE, index=False)

print(f"\n✔ Saved → {OUT_FILE}")