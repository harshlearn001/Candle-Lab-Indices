#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from pathlib import Path
from datetime import datetime

# =====================================================
# HEADER
# =====================================================
print("╭──────────────────────────────╮")
print("│ INDEX PCR ENGINE (FULL)     │")
print("│ All Snapshots + All PCR     │")
print("╰──────────────────────────────╯\n")

# =====================================================
# PATHS
# =====================================================
BASE_DIR = Path(r"H:\MarketForge\data\master\option_master\INDICES")

# ✅ KEEP SEPARATE (OPTIONS DATA)
OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\Options")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = ["NIFTY", "BANKNIFTY", "FINNIFTY"]

all_files = list(BASE_DIR.glob("*"))
print(f"Loaded Files: {len(all_files)}")

rows = []
all_dates = []

# =====================================================
# PROCESS FILES
# =====================================================
for file in all_files:

    if file.suffix not in [".csv", ".parquet"]:
        continue

    try:
        df = pd.read_parquet(file) if file.suffix == ".parquet" else pd.read_csv(file)

        if df.empty:
            continue

        df.columns = df.columns.str.upper().str.strip()

        # DATE FROM FILE
        try:
            file_date = datetime.fromtimestamp(file.stat().st_mtime)
            all_dates.append(file_date)
        except:
            file_date = None

        # OI FIX
        if "OPEN_INT" not in df.columns:
            if "OPENINTEREST" in df.columns:
                df["OPEN_INT"] = df["OPENINTEREST"]
            elif "OI" in df.columns:
                df["OPEN_INT"] = df["OI"]
            else:
                continue

        if not {"SYMBOL", "OPT_TYPE", "OPEN_INT"}.issubset(df.columns):
            continue

        symbol = str(df["SYMBOL"].iloc[0]).upper()

        if symbol not in TARGETS:
            continue

        ce_oi = df[df["OPT_TYPE"] == "CE"]["OPEN_INT"].sum()
        pe_oi = df[df["OPT_TYPE"] == "PE"]["OPEN_INT"].sum()

        if ce_oi == 0:
            continue

        pcr = pe_oi / ce_oi

        # =====================================================
        # SIGNAL LOGIC
        # =====================================================
        if pcr > 1.3:
            signal = "EXTREME_BULLISH"
            direction = "Bullish"
        elif pcr > 1.1:
            signal = "BULLISH"
            direction = "Bullish"
        elif pcr < 0.7:
            signal = "EXTREME_BEARISH"
            direction = "Bearish"
        elif pcr < 0.9:
            signal = "BEARISH"
            direction = "Bearish"
        else:
            signal = "NEUTRAL"
            direction = "Neutral"

        rows.append({
            "Index": symbol,
            "Pattern": "PCR",
            "Direction": direction,
            "Date": file_date.strftime("%Y-%m-%d") if file_date else "NA",
            "File": file.name,
            "CE_OI": int(ce_oi),
            "PE_OI": int(pe_oi),
            "PCR": round(pcr, 2),
            "Signal": signal
        })

    except Exception as e:
        print(f"Error in {file.name}: {e}")
        continue

# =====================================================
# BUILD DATAFRAME
# =====================================================
df = pd.DataFrame(rows)

# =====================================================
# FINAL DATE
# =====================================================
if all_dates:
    final_date = max(all_dates).strftime("%Y-%m-%d")
else:
    final_date = datetime.now().strftime("%Y-%m-%d")

OUT_FILE = OUT_DIR / f"index_pcr_full_{final_date}.csv"

print(f"\n📅 Data Date Used: {final_date}")

# =====================================================
# ALWAYS SAVE
# =====================================================
if df.empty:
    df = pd.DataFrame({
        "Message": ["No PCR data found"],
        "Date": [final_date]
    })
else:
    df = df.sort_values(["Index", "Date"], ascending=[True, False])

    print("\n📊 ALL PCR DATA")
    print(df.to_string(index=False))

# SAVE
df.to_csv(OUT_FILE, index=False)

print(f"\n✔ Saved → {OUT_FILE}")