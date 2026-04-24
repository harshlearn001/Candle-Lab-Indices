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
    "[bold red]INDEX HANGING MAN[/bold red]\n[cyan]Top Reversal Engine[/cyan]",
    border_style="red"
))

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")

OUT_DIR = Path(r"H:\Candle-Lab-Indices\analysis\index\candle_patterns")
OUT_DIR.mkdir(parents=True, exist_ok=True)

signals = []
all_dates = []   # ✅ FIX
files = list(INDEX_DIR.glob("*.csv"))

# =====================================================
# SWING HIGH FUNCTION
# =====================================================
def is_near_swing_high(df, i, lookback=10):
    if i - lookback < 0:
        return False
    recent_high = df['HIGH'].iloc[i-lookback:i].max()
    current_high = df['HIGH'].iloc[i]
    return current_high >= 0.95 * recent_high

# =====================================================
# MAIN LOOP
# =====================================================
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

        if len(df) < 220:
            continue

        # ✅ collect date
        all_dates.append(df["DATE"].max())

        # =====================================================
        # INDICATORS
        # =====================================================
        df['EMA50'] = df['CLOSE'].ewm(span=50).mean()
        df['SMA200'] = df['CLOSE'].rolling(window=200).mean()

        # =====================================================
        # LAST 5 CANDLES
        # =====================================================
        for i in range(-5, 0):

            row = df.iloc[i]

            open_ = row['OPEN']
            close = row['CLOSE']
            high = row['HIGH']
            low = row['LOW']

            body = abs(close - open_)
            candle_range = high - low

            if candle_range == 0 or body == 0:
                continue

            upper = high - max(open_, close)
            lower = min(open_, close) - low

            structure = (
                lower >= 1.5 * body and
                upper <= body
            )

            body_top = max(open_, close)
            position = body_top >= (high - candle_range * 0.4)

            trend = (
                close > df['EMA50'].iloc[i] and
                df['EMA50'].iloc[i] > df['SMA200'].iloc[i]
            )

            location = is_near_swing_high(df, i)

            if structure and position and trend and location:

                strength = lower / body
                rating = "STRONG" if strength > 3 else "NORMAL"

                signals.append({
                    "Index": file.stem,
                    "Date": row['DATE'].strftime("%Y-%m-%d"),
                    "Close": round(close, 2),
                    "Strength": round(strength, 2),
                    "Type": rating
                })

                break

    except:
        continue

# =====================================================
# FINAL DATE
# =====================================================
if all_dates:
    final_date = max(all_dates).strftime("%Y-%m-%d")
else:
    final_date = datetime.now().strftime("%Y-%m-%d")

OUT_FILE = OUT_DIR / f"index_hangingman_{final_date}.csv"

console.print(f"[yellow]📅 Data Date Used: {final_date}[/yellow]")

# =====================================================
# SUMMARY
# =====================================================
console.rule("[bold red]HANGING MAN SUMMARY[/bold red]")

console.print(f"[cyan]📊 Total Checked:[/cyan] {len(files)}")
console.print(f"[red]🔥 Signals Found:[/red] {len(signals)}")

# =====================================================
# OUTPUT
# =====================================================
df_out = pd.DataFrame(signals)

if not df_out.empty:

    df_out = df_out.sort_values("Strength", ascending=False)

    table = Table(title="🔻 INDEX HANGING MAN")

    for col in df_out.columns:
        table.add_column(col, justify="center")

    for _, row in df_out.iterrows():

        color = "red" if row["Type"] == "STRONG" else "yellow"

        table.add_row(
            f"[{color}]{row['Index']}[/{color}]",
            row["Date"],
            str(row["Close"]),
            str(row["Strength"]),
            row["Type"]
        )

    console.print(table)

    df_out.to_csv(OUT_FILE, index=False)
    console.print(f"\n[bold red]✔ Saved → {OUT_FILE}[/bold red]")

else:
    console.print("\n[green]✔ No Top Exhaustion Found (Trend Strong)[/green]")