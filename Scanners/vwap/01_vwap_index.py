#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
from datetime import datetime

print("╭──────────────────────────────╮")
print("│ INDEX VWAP ENGINE           │")
print("│ Fair Value Detection        │")
print("╰──────────────────────────────╯\n")

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\vwap")
OUT_DIR.mkdir(parents=True, exist_ok=True)

results = []
checked = 0
all_dates = []   # ✅ FIX

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

        # =====================================================
        # 🔥 DATE FIX
        # =====================================================
        if df["DATE"].dtype in ["int64", "float64"]:
            df["DATE"] = pd.to_datetime(df["DATE"].astype(str), errors="coerce")
        else:
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

        df = df.dropna(subset=["DATE"])
        df = df[df["DATE"] > "2000-01-01"]
        df = df.sort_values("DATE")

        if len(df) < 30:
            continue

        # ✅ collect date
        all_dates.append(df["DATE"].max())

        checked += 1

        # =====================================================
        # VWAP (Rolling 20)
        # =====================================================
        df["TP"] = (df["HIGH"] + df["LOW"] + df["CLOSE"]) / 3
        df["VWAP"] = df["TP"].rolling(window=20).mean()

        df = df.dropna()

        latest = df.iloc[-1]

        price = latest["CLOSE"]
        vwap = latest["VWAP"]

        distance = ((price - vwap) / vwap) * 100

        # =====================================================
        # ZONE CLASSIFICATION
        # =====================================================
        if distance > 3:
            zone = "OVEREXTENDED"
        elif distance > 1:
            zone = "ABOVE_VWAP"
        elif distance < -3:
            zone = "DEEP_DISCOUNT"
        elif distance < -1:
            zone = "BELOW_VWAP"
        else:
            zone = "FAIR_VALUE"

        results.append({
            "Index": file.stem,
            "Date": latest["DATE"].strftime("%Y-%m-%d"),
            "Close": round(price, 2),
            "VWAP": round(vwap, 2),
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

OUT_FILE = OUT_DIR / f"index_vwap_{final_date}.csv"

print(f"\n📅 Data Date Used: {final_date}")

# =====================================================
# OUTPUT
# =====================================================
df_out = pd.DataFrame(results)

print("\n" + "─"*80)
print("📊 VWAP SUMMARY")
print("─"*80)
print(f"Checked: {checked}")

if not df_out.empty:

    df_out = df_out.sort_values("Distance_%", ascending=False)

    print("\n📊 INDEX VWAP STATUS")
    print(df_out)

    df_out.to_csv(OUT_FILE, index=False)
    print(f"\n✔ Saved → {OUT_FILE}")

    # =====================================================
    # MARKET INSIGHT
    # =====================================================
    print("\n🧠 MARKET INSIGHT")

    over = len(df_out[df_out["Zone"] == "OVEREXTENDED"])
    below = len(df_out[df_out["Zone"] == "BELOW_VWAP"])

    if over >= 5:
        print("⚠ Market stretched → pullback risk")
    elif below >= 5:
        print("🔥 Market discounted → bounce zone")
    else:
        print("⚖ Market near fair value")

else:
    print("\n❌ No VWAP data")