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
    "[bold cyan]INDEX INSIDE BAR[/bold cyan]\n[white]Volatility Compression[/white]",
    border_style="cyan"
))

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\candle_patterns")
OUT_DIR.mkdir(parents=True, exist_ok=True)

results = []
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

        if not {"DATE","HIGH","LOW","CLOSE","OPEN"}.issubset(df.columns):
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

        if len(df) < 5:
            continue

        # ✅ collect date
        all_dates.append(df["DATE"].max())

        today_row = df.iloc[-1]
        prev = df.iloc[-2]

        # =====================================================
        # INSIDE BAR
        # =====================================================
        if today_row["HIGH"] < prev["HIGH"] and today_row["LOW"] > prev["LOW"]:

            today_range = today_row["HIGH"] - today_row["LOW"]
            prev_range  = prev["HIGH"] - prev["LOW"]

            if prev_range == 0:
                continue

            compression = today_range / prev_range

            # TREND CONTEXT
            df["EMA20"] = df["CLOSE"].ewm(span=20).mean()
            trend = "UP" if today_row["CLOSE"] > df["EMA20"].iloc[-1] else "DOWN"

            strength = "STRONG" if compression < 0.5 else "NORMAL"

            results.append({
                "Index": file.stem,
                "Date": today_row["DATE"].strftime("%Y-%m-%d"),
                "Close": round(today_row["CLOSE"], 2),
                "Compression": round(compression, 2),
                "Trend": trend,
                "Strength": strength
            })

    except:
        continue

# =====================================================
# FINAL DATE
# =====================================================
if all_dates:
    final_date = max(all_dates).strftime("%Y-%m-%d")
else:
    final_date = datetime.now().strftime("%Y-%m-%d")

OUT_FILE = OUT_DIR / f"index_insidebar_{final_date}.csv"

console.print(f"[yellow]📅 Data Date Used: {final_date}[/yellow]")

# =====================================================
# SUMMARY
# =====================================================
console.rule("[bold cyan]INSIDE BAR SUMMARY[/bold cyan]")

console.print(f"[cyan]📊 Total Checked:[/cyan] {len(files)}")
console.print(f"[blue]🔥 Signals Found:[/blue] {len(results)}")

# =====================================================
# OUTPUT
# =====================================================
df_out = pd.DataFrame(results)

if not df_out.empty:

    df_out = df_out.sort_values("Compression")

    table = Table(title="🔵 INDEX INSIDE BAR")

    for col in df_out.columns:
        table.add_column(col, justify="center")

    for _, row in df_out.iterrows():

        color = "green" if row["Trend"] == "UP" else "red"

        table.add_row(
            f"[{color}]{row['Index']}[/{color}]",
            row["Date"],
            str(row["Close"]),
            str(row["Compression"]),
            row["Trend"],
            row["Strength"]
        )

    console.print(table)

    df_out.to_csv(OUT_FILE, index=False)
    console.print(f"\n[bold cyan]✔ Saved → {OUT_FILE}[/bold cyan]")

else:
    console.print("\n[yellow]⚠ No Inside Bar Found[/yellow]")