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
    "[bold magenta]INDEX NR7[/bold magenta]\n[white]Volatility Contraction[/white]",
    border_style="magenta"
))

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

# ✅ NEW FOLDER
OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\NR7")
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

        # =====================================================
        # CALCULATIONS
        # =====================================================
        df["RANGE"] = df["HIGH"] - df["LOW"]
        df["MA20"] = df["CLOSE"].rolling(20).mean()

        df = df.dropna()

        if len(df) < 7:
            continue

        last7 = df.tail(7)

        today_row = last7.iloc[-1]
        prev6 = last7.iloc[:-1]

        # =====================================================
        # NR7 CONDITION
        # =====================================================
        is_nr7 = today_row["RANGE"] < prev6["RANGE"].min()

        if is_nr7:

            compression = today_row["RANGE"] / prev6["RANGE"].mean()
            strength = "STRONG" if compression < 0.6 else "NORMAL"

            direction = "Bullish" if today_row["CLOSE"] > today_row["MA20"] else "Bearish"

            results.append({
                "Index": file.stem,
                "Pattern": "NR7",
                "Direction": direction,
                "Date": today_row["DATE"].strftime("%Y-%m-%d"),
                "Close": round(today_row["CLOSE"], 2),
                "Compression": round(compression, 2),
                "Strength": strength
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

OUT_FILE = OUT_DIR / f"index_nr7_{final_date}.csv"

# DEBUG
print(f"\nDEBUG → Files Checked: {len(files)}")
print(f"DEBUG → Signals Found: {len(results)}")
print(f"DEBUG → Saving to: {OUT_FILE}")

console.print(f"[yellow]📅 Data Date Used: {final_date}[/yellow]")

# =====================================================
# SUMMARY
# =====================================================
console.rule("[bold magenta]NR7 SUMMARY[/bold magenta]")

console.print(f"[cyan]📊 Total Checked:[/cyan] {len(files)}")
console.print(f"[magenta]🔥 Signals Found:[/magenta] {len(results)}")

# =====================================================
# OUTPUT
# =====================================================
df_out = pd.DataFrame(results)

# ALWAYS SAVE
if df_out.empty:
    df_out = pd.DataFrame({
        "Message": ["No NR7 Found"],
        "Date": [final_date]
    })
else:
    df_out = df_out.sort_values("Compression")

    table = Table(title="🟣 INDEX NR7")

    for col in df_out.columns:
        table.add_column(col, justify="center")

    for _, row in df_out.iterrows():

        color = "green" if row["Direction"] == "Bullish" else "red"

        table.add_row(
            f"[{color}]{row['Index']}[/{color}]",
            row["Pattern"],
            f"[{color}]{row['Direction']}[/{color}]",
            row["Date"],
            str(row["Close"]),
            str(row["Compression"]),
            row["Strength"]
        )

    console.print(table)

# SAVE FILE
df_out.to_csv(OUT_FILE, index=False)

console.print(f"\n[bold magenta]✔ Saved → {OUT_FILE}[/bold magenta]")