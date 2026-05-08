#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
from datetime import datetime

print("╭──────────────────────────────╮")
print("│ INDEX FAIR VALUE ENGINE     │")
print("│ Price Mean Deviation        │")
print("╰──────────────────────────────╯\n")

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\VWAP")
OUT_DIR.mkdir(parents=True, exist_ok=True)

results = []
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

        if not {"DATE","HIGH","LOW","CLOSE"}.issubset(df.columns):
            continue

        # DATE FIX
        if df["DATE"].dtype in ["int64", "float64"]:
            df["DATE"] = pd.to_datetime(df["DATE"].astype(str), errors="coerce")
        else:
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

        df = df.dropna(subset=["DATE"])
        df = df[df["DATE"] > "2000-01-01"]
        df = df.sort_values("DATE")

        if len(df) < 30:
            continue

        all_dates.append(df["DATE"].max())
        checked += 1

        # =====================================================
        # FAIR VALUE (TP MEAN)
        # =====================================================
        df["TP"] = (df["HIGH"] + df["LOW"] + df["CLOSE"]) / 3
        df["FairValue"] = df["TP"].rolling(window=20).mean()

        df = df.dropna()

        latest = df.iloc[-1]

        price = latest["CLOSE"]
        fv = latest["FairValue"]

        distance = ((price - fv) / fv) * 100

        # =====================================================
        # ZONE
        # =====================================================
        if distance > 3:
            zone = "OVEREXTENDED"
            direction = "Bearish"
        elif distance > 1:
            zone = "ABOVE"
            direction = "Bullish"
        elif distance < -3:
            zone = "DEEP_DISCOUNT"
            direction = "Bullish"
        elif distance < -1:
            zone = "BELOW"
            direction = "Bearish"
        else:
            zone = "FAIR"
            direction = "Neutral"

        results.append({
            "Index": file.stem,
            "Pattern": "FairValue",
            "Direction": direction,
            "Date": latest["DATE"].strftime("%Y-%m-%d"),
            "Close": round(price, 2),
            "FairValue": round(fv, 2),
            "Distance_%": round(distance, 2),
            "Zone": zone
        })

        print(f"{file.stem:12} → {zone} ({round(distance,2)}%)")

    except Exception as e:
        print(f"ERROR → {file.stem} | {e}")

# =====================================================
# FINAL DATE
# =====================================================
if all_dates:
    final_date = max(all_dates).strftime("%Y-%m-%d")
else:
    final_date = datetime.now().strftime("%Y-%m-%d")

OUT_FILE = OUT_DIR / f"index_fairvalue_{final_date}.csv"

print(f"\n📅 Data Date Used: {final_date}")

# =====================================================
# ALWAYS SAVE
# =====================================================
df_out = pd.DataFrame(results)

print("\n📊 SUMMARY")
print(f"Checked: {checked}")

if df_out.empty:
    df_out = pd.DataFrame({
        "Message": ["No Fair Value Data"],
        "Date": [final_date]
    })
else:
    df_out = df_out.sort_values("Distance_%", ascending=False)
    print(df_out)

df_out.to_csv(OUT_FILE, index=False)

print(f"\n✔ Saved → {OUT_FILE}")