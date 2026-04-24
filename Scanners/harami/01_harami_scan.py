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

# =====================================================
# HEADER
# =====================================================
console.print(Panel.fit(
    "[bold magenta]INDEX HARAMI[/bold magenta]\n[cyan]Pause / Reversal Signal[/cyan]",
    border_style="magenta"
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
# HARAMI LOGIC
# =====================================================
def detect_harami(df):

    df = df.copy()

    df['Prev_Open'] = df['OPEN'].shift(1)
    df['Prev_Close'] = df['CLOSE'].shift(1)

    prev_high = df[['Prev_Open','Prev_Close']].max(axis=1)
    prev_low  = df[['Prev_Open','Prev_Close']].min(axis=1)

    curr_high = df[['OPEN','CLOSE']].max(axis=1)
    curr_low  = df[['OPEN','CLOSE']].min(axis=1)

    inside = (curr_high < prev_high) & (curr_low > prev_low)

    df['Bullish_Harami'] = (
        (df['Prev_Close'] < df['Prev_Open']) &
        (df['CLOSE'] > df['OPEN']) &
        inside
    )

    df['Bearish_Harami'] = (
        (df['Prev_Close'] > df['Prev_Open']) &
        (df['CLOSE'] < df['OPEN']) &
        inside
    )

    return df

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

        if len(df) < 20:
            continue

        # ✅ collect date
        all_dates.append(df["DATE"].max())

        df = detect_harami(df)

        # TREND CONTEXT
        df['EMA20'] = df['CLOSE'].ewm(span=20).mean()

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        bullish_trend = prev['CLOSE'] < df['EMA20'].iloc[-2]
        bearish_trend = prev['CLOSE'] > df['EMA20'].iloc[-2]

        if latest['Bullish_Harami'] and bullish_trend:

            strength = abs(prev['CLOSE'] - prev['OPEN'])

            signals.append({
                "Index": file.stem,
                "Date": latest['DATE'].strftime("%Y-%m-%d"),
                "Close": round(latest['CLOSE'], 2),
                "Type": "BULLISH",
                "Strength": round(strength, 2)
            })

        elif latest['Bearish_Harami'] and bearish_trend:

            strength = abs(prev['CLOSE'] - prev['OPEN'])

            signals.append({
                "Index": file.stem,
                "Date": latest['DATE'].strftime("%Y-%m-%d"),
                "Close": round(latest['CLOSE'], 2),
                "Type": "BEARISH",
                "Strength": round(strength, 2)
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

OUT_FILE = OUT_DIR / f"index_harami_{final_date}.csv"

console.print(f"[yellow]📅 Data Date Used: {final_date}[/yellow]")

# =====================================================
# SUMMARY
# =====================================================
console.rule("[bold magenta]HARAMI SUMMARY[/bold magenta]")

console.print(f"[cyan]📊 Total Checked:[/cyan] {len(files)}")
console.print(f"[magenta]🔥 Signals Found:[/magenta] {len(signals)}")

# =====================================================
# OUTPUT
# =====================================================
df_out = pd.DataFrame(signals)

if not df_out.empty:

    df_out = df_out.sort_values("Strength", ascending=False)

    table = Table(title="🟣 INDEX HARAMI")

    for col in df_out.columns:
        table.add_column(col, justify="center")

    for _, row in df_out.iterrows():

        color = "green" if row["Type"] == "BULLISH" else "red"

        table.add_row(
            f"[{color}]{row['Index']}[/{color}]",
            row["Date"],
            str(row["Close"]),
            row["Type"],
            str(row["Strength"])
        )

    console.print(table)

    df_out.to_csv(OUT_FILE, index=False)
    console.print(f"\n[bold magenta]✔ Saved → {OUT_FILE}[/bold magenta]")

else:
    console.print("\n[yellow]⚠ No Harami Signals Found[/yellow]")