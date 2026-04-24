#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

print("╭──────────────────────────────╮")
print("│ INDEX SHOOTING STAR         │")
print("│ Top Exhaustion Engine       │")
print("╰──────────────────────────────╯\n")

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\candle_patterns")
OUT_DIR.mkdir(parents=True, exist_ok=True)

results = []
checked = 0
all_dates = []   # ✅ FIX

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

        if len(df) < 20:
            continue

        # ✅ collect latest date
        all_dates.append(df["DATE"].max())

        checked += 1

        # =====================================================
        # TREND FILTER
        # =====================================================
        df["EMA20"] = df["CLOSE"].ewm(span=20).mean()

        if not (df.iloc[-1]["CLOSE"] > df.iloc[-1]["EMA20"]):
            continue

        # =====================================================
        # CURRENT CANDLE
        # =====================================================
        c = df.iloc[-1]

        o, h, l, cl = c["OPEN"], c["HIGH"], c["LOW"], c["CLOSE"]

        rng = h - l
        if rng <= 0:
            continue

        body = abs(cl - o)
        upper = h - max(o, cl)
        lower = min(o, cl) - l

        body_pct  = body / rng
        upper_pct = upper / rng
        lower_pct = lower / rng

        # =====================================================
        # QUALITY FILTER
        # =====================================================
        recent_ranges = df.iloc[-10:-1]["HIGH"] - df.iloc[-10:-1]["LOW"]

        if rng < np.median(recent_ranges):
            continue

        # =====================================================
        # SHOOTING STAR LOGIC
        # =====================================================
        if (
            body_pct <= 0.35 and
            upper_pct >= 0.50 and
            lower_pct <= 0.20
        ):

            if upper_pct > 0.7:
                strength = "STRONG"
            elif upper_pct > 0.6:
                strength = "NORMAL"
            else:
                strength = "WEAK"

            results.append({
                "Index": file.stem,
                "Date": c["DATE"].strftime("%Y-%m-%d"),
                "Close": round(cl, 2),
                "UpperWick%": round(upper_pct*100,2),
                "Body%": round(body_pct*100,2),
                "Strength": strength
            })

            print(f"🔴 Shooting Star → {file.stem}")

    except Exception as e:
        print(f"ERROR → {file.stem} | {e}")

# =====================================================
# FINAL DATE
# =====================================================
if all_dates:
    final_date = max(all_dates).strftime("%Y-%m-%d")
else:
    final_date = datetime.now().strftime("%Y-%m-%d")

OUT_FILE = OUT_DIR / f"index_shooting_star_{final_date}.csv"

print(f"\n📅 Data Date Used: {final_date}")

# =====================================================
# OUTPUT
# =====================================================
df_out = pd.DataFrame(results)

print("\n" + "─"*80)
print("📊 INDEX SHOOTING STAR SUMMARY")
print("─"*80)
print(f"Checked: {checked}")
print(f"Signals: {len(df_out)}")

if not df_out.empty:

    df_out = df_out.sort_values("UpperWick%", ascending=False)

    print("\n🔴 TOP EXHAUSTION INDICES")
    print(df_out)

    df_out.to_csv(OUT_FILE, index=False)
    print(f"\n✔ Saved → {OUT_FILE}")

    print("\n🧠 MARKET INSIGHT")

    if len(df_out) >= 3:
        print("⚠ Broad market exhaustion")
    elif len(df_out) > 0:
        print("⚠ Selective exhaustion")
    else:
        print("🚫 No exhaustion signal")

else:
    print("\n❌ No Shooting Star found")