#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from pathlib import Path
import pandas as pd
from datetime import datetime

console = Console()

# =================================================
# HEADER
# =================================================
console.print(Panel.fit(
    "[bold blue]INDEX ACCUMULATION ENGINE[/bold blue]\n[cyan]Range Expansion Model[/cyan]",
    border_style="blue"
))

# =================================================
# PATHS
# =================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

# ✅ SAME MASTER FOLDER
OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\Green_Volume")
OUT_DIR.mkdir(parents=True, exist_ok=True)

results = []
all_dates = []

# =================================================
# MAIN LOOP
# =================================================
files = list(INDEX_DIR.glob("*.csv"))

for file in files:

    try:
        df = pd.read_csv(file)

        if df.empty:
            continue

        df.columns = [c.strip().upper() for c in df.columns]
        df.rename(columns={"TRADE_DATE": "DATE"}, inplace=True)

        required = {"DATE", "OPEN", "HIGH", "LOW", "CLOSE"}
        if not required.issubset(df.columns):
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

        # =================================================
        # 4 GREEN CANDLES
        # =================================================
        if not (last4["CLOSE"] > last4["OPEN"]).all():
            continue

        # =================================================
        # RANGE EXPANSION
        # =================================================
        ranges = (last4["HIGH"] - last4["LOW"]).values

        if not (ranges[0] < ranges[1] < ranges[2] < ranges[3]):
            continue

        # =================================================
        # METRICS
        # =================================================
        momentum = (last4["CLOSE"] - last4["OPEN"]).sum()
        range_growth = ranges[3] / ranges[0]

        strength = "STRONG" if range_growth > 2 else "NORMAL"

        results.append({
            "Index": file.stem,
            "Pattern": "Accumulation",
            "Direction": "Bullish",
            "Date": last4.iloc[-1]["DATE"].strftime("%Y-%m-%d"),
            "Close": round(last4.iloc[-1]["CLOSE"], 2),
            "RangeGrowth": round(range_growth, 2),
            "Momentum": round(momentum, 2),
            "Strength": strength
        })

    except Exception as e:
        print(f"[red]Error in {file.name}: {e}[/red]")
        continue

# =================================================
# FINAL DATE
# =================================================
if all_dates:
    final_date = max(all_dates).strftime("%Y-%m-%d")
else:
    final_date = datetime.now().strftime("%Y-%m-%d")

OUT_FILE = OUT_DIR / f"index_accumulation_{final_date}.csv"

# DEBUG
print(f"\nDEBUG → Files Checked: {len(files)}")
print(f"DEBUG → Signals Found: {len(results)}")
print(f"DEBUG → Saving to: {OUT_FILE}")

console.print(f"[yellow]📅 Data Date Used: {final_date}[/yellow]")

# =================================================
# SUMMARY
# =================================================
console.rule("[bold cyan]ACCUMULATION SUMMARY[/bold cyan]")

console.print(f"[cyan]📊 Total Checked:[/cyan] {len(files)}")
console.print(f"[blue]🔥 Signals Found:[/blue] {len(results)}")

# =================================================
# OUTPUT
# =================================================
df_out = pd.DataFrame(results)

# ALWAYS SAVE
if df_out.empty:
    df_out = pd.DataFrame({
        "Message": ["No Accumulation Found"],
        "Date": [final_date]
    })
else:
    df_out = df_out.sort_values("RangeGrowth", ascending=False).reset_index(drop=True)

    table = Table(title="🔵 INDEX ACCUMULATION")

    for col in df_out.columns:
        table.add_column(col, justify="center")

    for _, row in df_out.iterrows():

        color = "blue" if row["Strength"] == "STRONG" else "yellow"

        table.add_row(
            f"[{color}]{row['Index']}[/{color}]",
            row["Pattern"],
            f"[{color}]{row['Direction']}[/{color}]",
            row["Date"],
            str(row["Close"]),
            str(row["RangeGrowth"]),
            str(row["Momentum"]),
            row["Strength"]
        )

    console.print(table)

# SAVE FILE
df_out.to_csv(OUT_FILE, index=False)

console.print(f"\n[bold blue]✔ Saved → {OUT_FILE}[/bold blue]")