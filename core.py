"""Research-only data pipeline, backtesting, and simulated paper execution."""
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd

DB = Path(__file__).resolve().parents[1] / 'market_data.sqlite3'

def connect(path=DB):
    conn = sqlite3.connect(path)
    conn.execute('''CREATE TABLE IF NOT EXISTS prices (symbol TEXT NOT NULL, date TEXT NOT NULL, open REAL, high REAL, low REAL, close REAL NOT NULL, volume REAL, PRIMARY KEY(symbol,date))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS paper_orders (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, symbol TEXT NOT NULL, side TEXT NOT NULL, quantity REAL NOT NULL, price REAL NOT NULL, notional REAL NOT NULL)''')
    conn.commit()
    return conn

def clean_prices(frame):
    if frame.empty: raise ValueError('No price data returned')
    df = frame.copy()
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower().strip() for c in df.columns]
    required = {'open','high','low','close','volume'}
    if not required.issubset(df.columns): raise ValueError(f'Missing fields: {required-set(df.columns)}')
    df.index = pd.to_datetime(df.index, utc=True).tz_localize(None).normalize()
    df = df.loc[~df.index.duplicated(keep='last')].sort_index()
    for col in required: df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['close','open','high','low'])
    df = df[(df[['open','high','low','close']] > 0).all(axis=1)]
    df = df[(df.high >= df[['open','close','low']].max(axis=1)) & (df.low <= df[['open','close','high']].min(axis=1))]
    df['volume'] = df['volume'].fillna(0).clip(lower=0)
    if df.empty: raise ValueError('No valid rows after cleaning')
    return df[['open','high','low','close','volume']]

def download(symbol, period='2y'):
    import yfinance as yf
    symbol = symbol.strip().upper()
    if not symbol or not all(c.isalnum() or c in '.-^=' for c in symbol): raise ValueError('Invalid symbol')
    return clean_prices(yf.download(symbol, period=period, auto_adjust=True, progress=False, threads=False))

def save_prices(conn, symbol, df):
    rows = [(symbol, d.strftime('%Y-%m-%d'), *map(float, row)) for d,row in df.iterrows()]
    conn.executemany('INSERT OR REPLACE INTO prices(symbol,date,open,high,low,close,volume) VALUES (?,?,?,?,?,?,?)', rows)
    conn.commit()
    return len(rows)

def load_prices(conn, symbol):
    df = pd.read_sql_query('SELECT date,open,high,low,close,volume FROM prices WHERE symbol=? ORDER BY date',conn,params=(symbol,),parse_dates=['date'])
    if df.empty: return df
    return df.set_index('date')

def backtest(df, fast=20, slow=50, fee_bps=5, initial_cash=10000):
    """Long-only SMA crossover. Signal on close; exposure applied next bar. No leverage."""
    if fast >= slow or fast < 2: raise ValueError('Require 2 <= fast < slow')
    if len(df) < slow + 2: raise ValueError('Not enough historical data for selected windows')
    result = df.copy()
    result['fast_sma'] = result.close.rolling(fast).mean()
    result['slow_sma'] = result.close.rolling(slow).mean()
    result['signal'] = (result.fast_sma > result.slow_sma).astype(int)
    result.loc[result.slow_sma.isna(),'signal'] = 0
    result['position'] = result.signal.shift(1).fillna(0)
    result['turnover'] = result.position.diff().abs().fillna(result.position.abs())
    result['market_return'] = result.close.pct_change().fillna(0)
    result['strategy_return'] = result.position * result.market_return - result.turnover * fee_bps / 10000
    result['equity'] = initial_cash * (1 + result.strategy_return).cumprod()
    result['buy_hold'] = initial_cash * (1 + result.market_return).cumprod()
    result['drawdown'] = result.equity / result.equity.cummax() - 1
    total = result.equity.iloc[-1]/initial_cash-1
    years = max((result.index[-1]-result.index[0]).days/365.25, 1/365.25)
    vol = result.strategy_return.std() * np.sqrt(252)
    metrics = {'Total return':total, 'Annualized return':(result.equity.iloc[-1]/initial_cash)**(1/years)-1, 'Annualized volatility':vol, 'Sharpe (rf=0)':(result.strategy_return.mean()*252/vol if vol > 0 else np.nan), 'Max drawdown':result.drawdown.min(), 'Trades':int(result.turnover.sum())}
    return result, metrics

def paper_order(conn, symbol, side, quantity, price):
    """Record simulated orders only. Never communicates with a brokerage."""
    if side not in ('BUY','SELL') or quantity <= 0 or price <= 0: raise ValueError('Invalid simulated order')
    from datetime import datetime, timezone
    conn.execute('INSERT INTO paper_orders(created_at,symbol,side,quantity,price,notional) VALUES (?,?,?,?,?,?)', (datetime.now(timezone.utc).isoformat(),symbol,side,float(quantity),float(price),float(quantity*price)))
    conn.commit()

def orders(conn):
    return pd.read_sql_query('SELECT * FROM paper_orders ORDER BY id DESC',conn)
