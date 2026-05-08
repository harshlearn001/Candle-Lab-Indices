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

# =====================================================
# HEADER
# =====================================================
console.print(Panel.fit(
    "[bold green]INDEX HAMMER + CONFIRMATION[/bold green]\n[cyan]Reversal Entry Engine[/cyan]",
    border_style="green"
))

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

# ✅ SAME MASTER FOLDER
OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\Hammer")
OUT_DIR.mkdir(parents=True, exist_ok=True)

all_dates = []

# =====================================================
# HAMMER DETECTION
# =====================================================
def detect_hammer(df):

    df = df.copy()

    df['range'] = df['HIGH'] - df['LOW']
    df = df[df['range'] > 0]

    df['body'] = abs(df['CLOSE'] - df['OPEN'])
    df['upper_shadow'] = df['HIGH'] - df[['OPEN','CLOSE']].max(axis=1)
    df['lower_shadow'] = df[['OPEN','CLOSE']].min(axis=1) - df['LOW']

    df['body_pct'] = df['body'] / df['range']
    df['lower_shadow_pct'] = df['lower_shadow'] / df['range']
    df['upper_shadow_pct'] = df['upper_shadow'] / df['range']

    structure = (
        (df['body_pct'] <= 0.30) &
        (df['lower_shadow_pct'] >= 0.60) &
        (df['upper_shadow_pct'] <= 0.10)
    )

    df['EMA5'] = df['CLOSE'].ewm(span=5, adjust=False).mean()
    trend = df['CLOSE'] < df['EMA5']

    df['Hammer'] = structure & trend

    return df

# =====================================================
# MAIN LOOP
# =====================================================
signals = []
files = list(INDEX_DIR.glob("*.csv"))

for file in files:

    try:
        df = pd.read_csv(file)

        if df.empty:
            continue

        df.columns = [c.strip().upper() for c in df.columns]
        df.rename(columns={"TRADE_DATE": "DATE"}, inplace=True)

        required = {'DATE','OPEN','HIGH','LOW','CLOSE'}
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

        df = detect_hammer(df)

        hammer = df.iloc[-2]
        confirm = df.iloc[-1]

        if hammer['Hammer']:

            breakout = confirm['CLOSE'] > hammer['HIGH']
            bullish = confirm['CLOSE'] > confirm['OPEN']

            if breakout and bullish:

                strength = confirm['CLOSE'] - hammer['HIGH']
                rating = "STRONG" if strength > (hammer['HIGH'] * 0.01) else "NORMAL"

                signals.append({
                    "Index": file.stem,
                    "Pattern": "Hammer",
                    "Direction": "Bullish",
                    "Date": confirm['DATE'].strftime("%Y-%m-%d"),
                    "Close": round(confirm['CLOSE'], 2),
                    "Strength": round(strength, 2),
                    "Type": rating
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

OUT_FILE = OUT_DIR / f"index_hammer_{final_date}.csv"

# DEBUG
print(f"\nDEBUG → Files Checked: {len(files)}")
print(f"DEBUG → Signals Found: {len(signals)}")
print(f"DEBUG → Saving to: {OUT_FILE}")

console.print(f"[yellow]📅 Data Date Used: {final_date}[/yellow]")

# =====================================================
# SUMMARY
# =====================================================
console.rule("[bold green]HAMMER SUMMARY[/bold green]")

console.print(f"[cyan]📊 Total Checked:[/cyan] {len(files)}")
console.print(f"[green]🔥 Signals Found:[/green] {len(signals)}")

# =====================================================
# OUTPUT
# =====================================================
df_out = pd.DataFrame(signals)

# ALWAYS SAVE
if df_out.empty:
    df_out = pd.DataFrame({
        "Message": ["No Hammer Found"],
        "Date": [final_date]
    })
else:
    df_out = df_out.sort_values("Strength", ascending=False)

    table = Table(title="🟢 INDEX HAMMER + CONFIRMATION")

    for col in df_out.columns:
        table.add_column(col, justify="center")

    for _, row in df_out.iterrows():

        color = "green" if row["Type"] == "STRONG" else "yellow"

        table.add_row(
            f"[{color}]{row['Index']}[/{color}]",
            row["Pattern"],
            f"[{color}]{row['Direction']}[/{color}]",
            row["Date"],
            str(row["Close"]),
            str(row["Strength"]),
            row["Type"]
        )

    console.print(table)

# SAVE FILE
df_out.to_csv(OUT_FILE, index=False)

console.print(f"\n[bold green]✔ Saved → {OUT_FILE}[/bold green]")