#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

import pandas as pd
from pathlib import Path
from datetime import datetime

console = Console()

# =====================================================
# HEADER
# =====================================================
console.print(Panel.fit(
    "[bold red]INDEX EVENING STAR[/bold red]\n[white]Top Reversal Engine[/white]",
    border_style="red"
))

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

# ✅ NEW FOLDER
OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\EveningStar")
OUT_DIR.mkdir(parents=True, exist_ok=True)

results = []
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

        if len(df) < 5:
            continue

        all_dates.append(df["DATE"].max())

        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]

        # =====================================================
        # EVENING STAR LOGIC
        # =====================================================
        cond1 = c1["CLOSE"] > c1["OPEN"]

        body2 = abs(c2["CLOSE"] - c2["OPEN"])
        range2 = c2["HIGH"] - c2["LOW"]
        cond2 = range2 > 0 and body2 < (0.3 * range2)

        cond3 = (
            c3["CLOSE"] < c3["OPEN"] and
            c3["CLOSE"] < (c1["OPEN"] + c1["CLOSE"]) / 2
        )

        if cond1 and cond2 and cond3:

            strength = abs(c1["CLOSE"] - c3["CLOSE"])
            level = "STRONG" if strength > (0.02 * c3["CLOSE"]) else "NORMAL"

            results.append({
                "Index": file.stem,
                "Pattern": "EveningStar",
                "Direction": "Bearish",
                "Date": c3["DATE"].strftime("%Y-%m-%d"),
                "Close": round(c3["CLOSE"], 2),
                "StrengthPts": round(strength, 2),
                "Strength": level
            })

    except Exception as e:
        print(f"[red]Error in {file.name}: {e}[/red]")
        continue

# =====================================================
# FINAL DATE
# =====================================================
if all_dates:
    final_date = max(all_dates).strftime("%Y-%m-%d")
else:
    final_date = datetime.now().strftime("%Y-%m-%d")

OUT_FILE = OUT_DIR / f"index_eveningstar_{final_date}.csv"

# DEBUG
print(f"\nDEBUG → Files Checked: {len(files)}")
print(f"DEBUG → Signals Found: {len(results)}")
print(f"DEBUG → Saving to: {OUT_FILE}")

console.print(f"[yellow]📅 Data Date Used: {final_date}[/yellow]")

# =====================================================
# SUMMARY
# =====================================================
console.rule("[bold red]EVENING STAR SUMMARY[/bold red]")

console.print(f"[cyan]📊 Total Checked:[/cyan] {len(files)}")
console.print(f"[red]🔥 Signals Found:[/red] {len(results)}")

# =====================================================
# OUTPUT
# =====================================================
df_out = pd.DataFrame(results)

# ALWAYS SAVE
if df_out.empty:
    df_out = pd.DataFrame({
        "Message": ["No Evening Star Found"],
        "Date": [final_date]
    })
else:
    df_out = df_out.sort_values("StrengthPts", ascending=False)

    table = Table(title="🌇 INDEX EVENING STAR")

    for col in df_out.columns:
        table.add_column(col, justify="center")

    for _, row in df_out.iterrows():

        color = "red" if row["Direction"] == "Bearish" else "white"

        table.add_row(
            f"[{color}]{row['Index']}[/{color}]",
            row["Pattern"],
            f"[{color}]{row['Direction']}[/{color}]",
            row["Date"],
            str(row["Close"]),
            str(row["StrengthPts"]),
            row["Strength"]
        )

    console.print(table)

# SAVE FILE
df_out.to_csv(OUT_FILE, index=False)

console.print(f"\n[bold red]✔ Saved → {OUT_FILE}[/bold red]")