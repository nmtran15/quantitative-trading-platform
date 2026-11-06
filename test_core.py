import sqlite3
import numpy as np
import pandas as pd
import pytest
from src.core import clean_prices,connect,save_prices,load_prices,backtest,paper_order,orders

def sample(n=100):
    idx = pd.date_range('2024-01-01',periods=n,freq='B')
    x = np.linspace(100,130,n)
    return pd.DataFrame({'open':x,'high':x+1,'low':x-1,'close':x,'volume':1000},index=idx)

def test_pipeline(tmp_path):
    df=clean_prices(sample())
    conn=connect(tmp_path/'test.sqlite')
    assert save_prices(conn,'TEST',df)==100
    assert len(load_prices(conn,'TEST'))==100
    bt,stats=backtest(df)
    assert len(bt)==100
    assert 'Max drawdown' in stats
    paper_order(conn,'TEST','BUY',2,100)
    assert orders(conn).iloc[0]['notional']==200

def test_invalid_windows():
    with pytest.raises(ValueError): backtest(sample(),50,20)
