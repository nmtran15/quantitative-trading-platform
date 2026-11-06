# Quant Trading Lab

A locally runnable quantitative research dashboard with Yahoo Finance ingestion, validation, SQLite storage, interactive Plotly charts, an SMA crossover backtest, and **simulated** trade logging. Includes a standalone C++ moving-average demonstration.

## Quick start

Requires Python 3.10+ and internet for market data downloads.

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

In the sidebar, enter a ticker (e.g. SPY), select a date range, and click **Download and store**. The dashboard will display prices and a backtest. The SQLite database is created automatically in the project directory.

Run tests: `python -m pytest -q`

## C++ component

`cpp/indicators.cpp` is a **standalone** C++ moving-average implementation, not yet wired into the Python application. On a machine with g++:

```bash
g++ -O2 -std=c++17 cpp/indicators.cpp -o indicators
printf '3\n1\n2\n3\n4\n' | ./indicators
```

## Important limitations

- **No Bloomberg integration**: requires an authorized Bloomberg Terminal/API entitlement and an environment with Bloomberg libraries. A licensed connector can be added later.
- **No real trade execution**: the paper order ledger only stores hypothetical transactions; it does not connect to a broker, track account balances, or enforce risk limits.
- Yahoo Finance data may be delayed, incomplete, or subject to usage restrictions; check provider terms before deployment.
- The SMA backtest is educational, not investment advice. Signals use close prices and take effect on the following bar; transaction fees are modeled but execution/slippage and numerous market frictions are simplified. Do not use performance as evidence of a profitable live strategy.
- SQLite is local and single-user; production systems require security, monitoring, robust data validation, and operational controls.

## Next steps

Add a broker's **sandbox/paper trading API**, a portfolio ledger and risk controls, parameter-sensitivity tests, out-of-sample validation, and a properly licensed Bloomberg connector. Benchmark the C++ module before integrating it via a binding.
