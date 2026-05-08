#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

console = Console()

# =================================================
# HEADER
# =================================================
console.print(Panel.fit(
    "[bold magenta]INDEX GRAVESTONE DOJI[/bold magenta]\n[cyan]Reversal Exhaustion Engine[/cyan]",
    border_style="magenta"
))

# =================================================
# PATHS
# =================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

# ✅ SAME FOLDER AS ENGULFING
OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\Gravestone")
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

        if len(df) < 10:
            continue

        all_dates.append(df["DATE"].max())

        # UPTREND CHECK
        if df.iloc[-3]["CLOSE"] <= df.iloc[-6]["CLOSE"]:
            continue

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

        # RANGE QUALITY
        recent_ranges = df.iloc[-10:-1]["HIGH"] - df.iloc[-10:-1]["LOW"]
        if rng < np.median(recent_ranges):
            continue

        # GRAVESTONE CONDITION
        if (
            body_pct <= 0.25 and
            upper_pct >= 0.45 and
            lower_pct <= 0.20
        ):

            symbol = file.stem

            strength = "STRONG" if upper_pct >= 0.65 else "NORMAL"

            results.append({
                "Index": symbol,
                "Pattern": "Gravestone",
                "Direction": "Bearish",
                "Date": c["DATE"].strftime("%Y-%m-%d"),
                "Close": round(cl, 2),
                "UpperWick%": round(upper_pct * 100, 2),
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

OUT_FILE = OUT_DIR / f"index_gravestone_{final_date}.csv"

# DEBUG
print(f"\nDEBUG → Files Checked: {len(files)}")
print(f"DEBUG → Signals Found: {len(results)}")
print(f"DEBUG → Saving to: {OUT_FILE}")

console.print(f"[yellow]📅 Data Date Used: {final_date}[/yellow]")

# =================================================
# SUMMARY
# =================================================
console.rule("[bold magenta]GRAVESTONE SUMMARY[/bold magenta]")

console.print(f"[cyan]📊 Total Checked:[/cyan] {len(files)}")
console.print(f"[magenta]🔥 Signals Found:[/magenta] {len(results)}")

# =================================================
# OUTPUT
# =================================================
df_out = pd.DataFrame(results)

# ALWAYS SAVE
if df_out.empty:
    df_out = pd.DataFrame({
        "Message": ["No Gravestone Doji Found"],
        "Date": [final_date]
    })
else:
    df_out = df_out.sort_values("UpperWick%", ascending=False).reset_index(drop=True)

    table = Table(title="🟣 INDEX GRAVESTONE DOJI")

    for col in df_out.columns:
        table.add_column(col, justify="center")

    for _, row in df_out.iterrows():

        color = "magenta" if row["Strength"] == "STRONG" else "yellow"

        table.add_row(
            f"[{color}]{row['Index']}[/{color}]",
            row["Pattern"],
            f"[{color}]{row['Direction']}[/{color}]",
            row["Date"],
            str(row["Close"]),
            str(row["UpperWick%"]),
            row["Strength"]
        )

    console.print(table)

# SAVE FILE
df_out.to_csv(OUT_FILE, index=False)

console.print(f"\n[bold magenta]✔ Saved → {OUT_FILE}[/bold magenta]")