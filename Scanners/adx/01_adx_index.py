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
OUT_DIR   = Path(r"H:\Candle-Lab-Indices\analysis\index\adx")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================
# DATE STORAGE
# =====================================================
all_dates = []

# =====================================================
# ADX CALCULATION
# =====================================================
def calculate_adx(df, period=14):

    df = df.copy()

    df['TR'] = np.maximum.reduce([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ])

    df['+DM'] = np.where(
        (df['High'] - df['High'].shift()) > (df['Low'].shift() - df['Low']),
        np.maximum(df['High'] - df['High'].shift(), 0),
        0
    )

    df['-DM'] = np.where(
        (df['Low'].shift() - df['Low']) > (df['High'] - df['High'].shift()),
        np.maximum(df['Low'].shift() - df['Low'], 0),
        0
    )

    TR_n = df['TR'].rolling(period).sum()
    plus_DM_n = df['+DM'].rolling(period).sum()
    minus_DM_n = df['-DM'].rolling(period).sum()

    df['+DI'] = 100 * (plus_DM_n / TR_n)
    df['-DI'] = 100 * (minus_DM_n / TR_n)

    df['DX'] = 100 * abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])
    df['ADX'] = df['DX'].rolling(period).mean()

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

        df.rename(columns={
            "TRADE_DATE": "Date",
            "OPEN": "Open",
            "HIGH": "High",
            "LOW": "Low",
            "CLOSE": "Close"
        }, inplace=True)

        if not {'Date','Open','High','Low','Close'}.issubset(df.columns):
            continue

        # =====================================================
        # 🔥 DATE FIX (CRITICAL)
        # =====================================================
        if df["Date"].dtype in ["int64", "float64"]:
            df["Date"] = pd.to_datetime(df["Date"].astype(str), errors="coerce")
        else:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        df = df.dropna(subset=["Date"])

        # REMOVE BAD 1970 DATES
        df = df[df["Date"] > "2000-01-01"]

        df = df.sort_values("Date")

        if len(df) < 50:
            continue

        # ✅ COLLECT VALID DATE
        if not df.empty:
            all_dates.append(df["Date"].max())

        df = calculate_adx(df)

        latest = df.iloc[-1]

        adx = latest['ADX']
        plus_di = latest['+DI']
        minus_di = latest['-DI']

        symbol = file.stem

        signal = None

        if adx < 20:
            signal = "WEAK"
            weak_count += 1

        elif adx > 25:
            if plus_di > minus_di:
                signal = "UPTREND"
                uptrend_count += 1
            elif minus_di > plus_di:
                signal = "DOWNTREND"
                downtrend_count += 1

        if signal:
            signals.append({
                "Index": symbol,
                "Date": latest["Date"].strftime("%Y-%m-%d"),
                "Close": round(latest['Close'], 2),
                "ADX": round(adx, 2),
                "+DI": round(plus_di, 2),
                "-DI": round(minus_di, 2),
                "Signal": signal
            })

    except Exception as e:
        continue

# =====================================================
# FINAL DATE
# =====================================================
if all_dates:
    final_date = max(all_dates).strftime("%Y-%m-%d")
else:
    final_date = datetime.now().strftime("%Y-%m-%d")

OUT_FILE = OUT_DIR / f"index_adx_signals_{final_date}.csv"

console.print(f"[yellow]📅 Data Date Used: {final_date}[/yellow]")

# =====================================================
# SUMMARY
# =====================================================
console.rule("[bold cyan]INDEX ADX SUMMARY[/bold cyan]")

console.print(f"[green]🔥 Uptrend:[/green] {uptrend_count}")
console.print(f"[red]💀 Downtrend:[/red] {downtrend_count}")
console.print(f"[yellow]⚠ Weak:[/yellow] {weak_count}")

# =====================================================
# SAVE + DISPLAY
# =====================================================
signals_df = pd.DataFrame(signals)

if not signals_df.empty:

    signals_df = signals_df.sort_values("ADX", ascending=False)

    table = Table(title="📊 INDEX TREND STRENGTH")

    for col in signals_df.columns:
        table.add_column(col, justify="center")

    for _, row in signals_df.iterrows():
        color = "green" if row["Signal"] == "UPTREND" else "red" if row["Signal"] == "DOWNTREND" else "yellow"
        table.add_row(*[f"[{color}]{str(x)}[/{color}]" for x in row])

    console.print(table)

    signals_df.to_csv(OUT_FILE, index=False)
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