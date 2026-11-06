import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.core import connect, download, save_prices, load_prices, backtest, paper_order, orders

st.set_page_config(page_title='Quant Trading Lab', layout='wide', page_icon='📈')
st.title('Quant Trading Lab')
st.caption('Research dashboard • Yahoo Finance data • SQLite • SMA backtest • simulated paper orders only')
conn = connect()
with st.sidebar:
    st.header('Market data')
    symbol = st.text_input('Ticker', 'SPY').strip().upper()
    period = st.selectbox('History', ['6mo','1y','2y','5y','10y'], index=2)
    if st.button('Download and store', type='primary'):
        try:
            with st.spinner('Downloading and validating prices...'):
                frame = download(symbol,period)
                count = save_prices(conn,symbol,frame)
            st.success(f'Saved {count} cleaned daily observations')
        except Exception as e: st.error(f'Data retrieval failed: {e}')
    st.header('Strategy')
    fast = st.slider('Fast SMA', 2, 100, 20)
    slow = st.slider('Slow SMA', 5, 250, 50)
    fee = st.number_input('Transaction fee (bps)', min_value=0.0, max_value=100.0, value=5.0)
    capital = st.number_input('Starting capital ($)', min_value=100.0, value=10000.0, step=1000.0)

df = load_prices(conn,symbol)
if df.empty:
    st.info('Enter a ticker and click “Download and store” to begin. An internet connection is required for Yahoo Finance downloads.')
    st.stop()

st.subheader(f'{symbol} market overview')
a,b,c,d = st.columns(4)
a.metric('Latest close',f'${df.close.iloc[-1]:,.2f}')
b.metric('Observations',f'{len(df):,}')
c.metric('First date',str(df.index[0].date()))
d.metric('Last date',str(df.index[-1].date()))
fig = make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.06,row_heights=[.75,.25])
fig.add_trace(go.Candlestick(x=df.index,open=df.open,high=df.high,low=df.low,close=df.close,name='OHLC'),row=1,col=1)
fig.add_trace(go.Bar(x=df.index,y=df.volume,name='Volume'),row=2,col=1)
fig.update_layout(height=520,xaxis_rangeslider_visible=False,margin=dict(l=10,r=10,t=20,b=10))
st.plotly_chart(fig,use_container_width=True)
try:
    bt, metrics = backtest(df,fast,slow,fee,capital)
    st.subheader('SMA crossover backtest')
    st.caption('Daily close signals; exposure starts on the next daily bar. Simplified research model: close-to-close returns, no slippage, no financing costs, no corporate-action validation. Not a production execution simulation.')
    m1,m2,m3,m4 = st.columns(4)
    m1.metric('Total return',f'{metrics["Total return"]:.1%}')
    m2.metric('Annualized return',f'{metrics["Annualized return"]:.1%}')
    m3.metric('Max drawdown',f'{metrics["Max drawdown"]:.1%}')
    m4.metric('Sharpe (rf=0)',f'{metrics["Sharpe (rf=0)"]:.2f}')
    chart = go.Figure()
    chart.add_trace(go.Scatter(x=bt.index,y=bt.equity,name='Strategy'))
    chart.add_trace(go.Scatter(x=bt.index,y=bt.buy_hold,name='Buy and hold'))
    chart.update_layout(yaxis_title='Portfolio value ($)',height=380)
    st.plotly_chart(chart,use_container_width=True)
    st.write(f'Position changes: {metrics["Trades"]} | Latest generated signal: {"LONG" if bt.signal.iloc[-1] else "FLAT"}')
    with st.expander('Inspect cleaned data and indicators'):
        st.dataframe(bt.tail(100),use_container_width=True)
        st.download_button('Export analyzed CSV',bt.to_csv().encode(),file_name=f'{symbol}_analysis.csv',mime='text/csv')
except ValueError as e:
    st.warning(str(e))

st.subheader('Simulated order ledger')
st.caption('Records hypothetical orders in local SQLite. Does not place real orders or enforce portfolio buying power.')
with st.form('paper'):
    side = st.selectbox('Side',['BUY','SELL'])
    qty = st.number_input('Shares',min_value=0.01,value=1.0,step=1.0)
    submitted = st.form_submit_button('Record simulated order')
    if submitted:
        paper_order(conn,symbol,side,qty,float(df.close.iloc[-1]))
        st.success('Simulated order recorded. No brokerage order was submitted.')
st.dataframe(orders(conn),use_container_width=True)
