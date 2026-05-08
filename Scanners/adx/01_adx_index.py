#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

console = Console()

# =====================================================
# HEADER
# =====================================================
console.print(Panel.fit(
    "[bold green]ADX INDEX SCANNER[/bold green]\n[cyan]Trend Strength Engine[/cyan]",
    border_style="green"
))

# =====================================================
# PATHS
# =====================================================
INDEX_DIR = Path(r"H:\MarketForge\data\master\Indices_master")
OUT_DIR   = Path(r"H:\Candle-Lab-Indices\analysis\index\ADX")
OUT_DIR.mkdir(parents=True, exist_ok=True)

all_dates = []

# =====================================================
# ADX (WILDER)
# =====================================================
def calculate_adx(df, period=14):

    df = df.copy()

    df['TR'] = np.maximum.reduce([
        df['HIGH'] - df['LOW'],
        abs(df['HIGH'] - df['CLOSE'].shift()),
        abs(df['LOW'] - df['CLOSE'].shift())
    ])

    df['+DM'] = np.where(
        (df['HIGH'] - df['HIGH'].shift()) > (df['LOW'].shift() - df['LOW']),
        np.maximum(df['HIGH'] - df['HIGH'].shift(), 0),
        0
    )

    df['-DM'] = np.where(
        (df['LOW'].shift() - df['LOW']) > (df['HIGH'] - df['HIGH'].shift()),
        np.maximum(df['LOW'].shift() - df['LOW'], 0),
        0
    )

    TR_n = df['TR'].ewm(alpha=1/period, adjust=False).mean()
    plus_DM_n = df['+DM'].ewm(alpha=1/period, adjust=False).mean()
    minus_DM_n = df['-DM'].ewm(alpha=1/period, adjust=False).mean()

    df['+DI'] = 100 * (plus_DM_n / TR_n)
    df['-DI'] = 100 * (minus_DM_n / TR_n)

    df['DX'] = 100 * abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])
    df['ADX'] = df['DX'].ewm(alpha=1/period, adjust=False).mean()

    return df

# =====================================================
# MAIN LOOP
# =====================================================
files = list(INDEX_DIR.glob("*.csv"))

signals = []
uptrend_count = 0
downtrend_count = 0
weak_count = 0

for file in files:

    try:
        df = pd.read_csv(file)

        df.columns = [c.strip().upper() for c in df.columns]
        df.rename(columns={"TRADE_DATE": "DATE"}, inplace=True)

        if not {'DATE','OPEN','HIGH','LOW','CLOSE'}.issubset(df.columns):
            continue

        # DATE FIX
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
        df = df.dropna(subset=["DATE"])
        df = df[df["DATE"] > "2000-01-01"]
        df = df.sort_values("DATE")

        if len(df) < 50:
            continue

        all_dates.append(df["DATE"].max())

        df = calculate_adx(df)

        latest = df.iloc[-1]

        adx = latest['ADX']
        plus_di = latest['+DI']
        minus_di = latest['-DI']

        symbol = file.stem

        # =====================================================
        # CLASSIFICATION
        # =====================================================
        if adx < 20:
            direction = "Neutral"
            strength = "WEAK"
            weak_count += 1

        elif adx > 25:
            if plus_di > minus_di:
                direction = "Bullish"
                uptrend_count += 1
            else:
                direction = "Bearish"
                downtrend_count += 1

            if adx > 40:
                strength = "STRONG"
            else:
                strength = "NORMAL"

        else:
            continue

        signals.append({
            "Index": symbol,
            "Pattern": "ADX",
            "Direction": direction,
            "Date": latest["DATE"].strftime("%Y-%m-%d"),
            "Close": round(latest['CLOSE'], 2),
            "ADX": round(adx, 2),
            "+DI": round(plus_di, 2),
            "-DI": round(minus_di, 2),
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

OUT_FILE = OUT_DIR / f"index_adx_{final_date}.csv"

console.print(f"[yellow]📅 Data Date Used: {final_date}[/yellow]")

# =====================================================
# ALWAYS SAVE
# =====================================================
df_out = pd.DataFrame(signals)

if df_out.empty:
    df_out = pd.DataFrame({
        "Message": ["No ADX Signals"],
        "Date": [final_date]
    })
else:
    df_out = df_out.sort_values("ADX", ascending=False)

df_out.to_csv(OUT_FILE, index=False)

console.print(f"\n[bold green]✔ Saved → {OUT_FILE}[/bold green]")

# =====================================================
# MARKET INSIGHT
# =====================================================
console.rule("[bold yellow]MARKET INSIGHT[/bold yellow]")

total = uptrend_count + downtrend_count + weak_count

if total > 0:
    up_pct = (uptrend_count / total) * 100
    down_pct = (downtrend_count / total) * 100

    if up_pct > 50:
        console.print("[bold green]✔ Bullish Market Bias[/bold green]")
    elif down_pct > 50:
        console.print("[bold red]✔ Bearish Market Bias[/bold red]")
    else:
        console.print("[yellow]✔ Sideways Market[/yellow]")