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
    "[bold red]INDEX BEARISH ENGULFING[/bold red]\n[cyan]Price Action Engine[/cyan]",
    border_style="red"
))

# =================================================
# PATHS
# =================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\candle_patterns")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =================================================
# PARAMETERS
# =================================================
MIN_BODY_RATIO = 0.40

results = []
all_dates = []   # ✅ IMPORTANT

# =================================================
# MAIN LOOP
# =================================================
files = list(INDEX_DIR.glob("*.csv"))

for file in files:

    try:
        df = pd.read_csv(file)

        if len(df) < 2:
            continue

        df.columns = [c.strip().upper() for c in df.columns]

        df.rename(columns={
            "TRADE_DATE": "DATE"
        }, inplace=True)

        required = {"DATE", "OPEN", "HIGH", "LOW", "CLOSE"}
        if not required.issubset(df.columns):
            continue

        # =================================================
        # 🔥 DATE FIX
        # =================================================
        if df["DATE"].dtype in ["int64", "float64"]:
            df["DATE"] = pd.to_datetime(df["DATE"].astype(str), errors="coerce")
        else:
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

        df = df.dropna(subset=["DATE"])
        df = df[df["DATE"] > "2000-01-01"]
        df = df.sort_values("DATE")

        if len(df) < 2:
            continue

        # ✅ collect date
        all_dates.append(df["DATE"].max())

        prev = df.iloc[-2]
        curr = df.iloc[-1]

        # =================================================
        # BODY RATIO
        # =================================================
        def body_ratio(c):
            rng = c["HIGH"] - c["LOW"]
            if rng <= 0:
                return 0
            return abs(c["CLOSE"] - c["OPEN"]) / rng

        if body_ratio(prev) < MIN_BODY_RATIO:
            continue

        if body_ratio(curr) < MIN_BODY_RATIO:
            continue

        # =================================================
        # 🔴 BEARISH ENGULFING
        # =================================================
        if (
            prev["CLOSE"] > prev["OPEN"] and
            curr["CLOSE"] < curr["OPEN"] and
            curr["OPEN"]  > prev["CLOSE"] and
            curr["CLOSE"] < prev["OPEN"]
        ):

            symbol = file.stem

            body_size = abs(curr["CLOSE"] - curr["OPEN"])
            prev_body = abs(prev["CLOSE"] - prev["OPEN"])
            strength = "STRONG" if body_size > prev_body else "NORMAL"

            results.append({
                "Index": symbol,
                "Date": curr["DATE"].strftime("%Y-%m-%d"),
                "Close": round(curr["CLOSE"], 2),
                "Strength": strength
            })

    except:
        continue

# =================================================
# FINAL DATE
# =================================================
if all_dates:
    final_date = max(all_dates).strftime("%Y-%m-%d")
else:
    final_date = datetime.now().strftime("%Y-%m-%d")

OUT_FILE = OUT_DIR / f"index_bearish_engulfing_{final_date}.csv"

console.print(f"[yellow]📅 Data Date Used: {final_date}[/yellow]")

# =================================================
# SUMMARY
# =================================================
console.rule("[bold cyan]ENGULFING SUMMARY[/bold cyan]")

console.print(f"[cyan]📊 Total Checked:[/cyan] {len(files)}")
console.print(f"[red]🔥 Signals Found:[/red] {len(results)}")

# =================================================
# OUTPUT
# =================================================
df_out = pd.DataFrame(results)

if not df_out.empty:

    df_out = df_out.sort_values("Date", ascending=False).reset_index(drop=True)

    table = Table(title="🔴 INDEX BEARISH ENGULFING")

    for col in df_out.columns:
        table.add_column(col, justify="center")

    for _, row in df_out.iterrows():

        color = "red" if row["Strength"] == "STRONG" else "yellow"

        table.add_row(
            f"[{color}]{row['Index']}[/{color}]",
            f"[{color}]{row['Date']}[/{color}]",
            f"[{color}]{row['Close']}[/{color}]",
            f"[{color}]{row['Strength']}[/{color}]"
        )

    console.print(table)

    df_out.to_csv(OUT_FILE, index=False)
    console.print(f"\n[bold red]✔ Saved → {OUT_FILE}[/bold red]")

else:
    console.print("\n[green]✔ No Bearish Engulfing Found[/green]")