from datetime import datetime 
import os 
import sys 
sys.path.append(os.path.join('..', 'pricing'))
sys.path.append(os.getcwd())
import pandas as pd
from alpha_vantage import AlphaVantage
import queue
from pytrade.datahandler import HistoricCSVDataHandler
from pytrade.portfolio import Portfolio
from pytrade.event import MarketEvent



if __name__ == "__main__":
# Create an AlphaVantage API instance
    av = AlphaVantage()
    # Download the Apple Group OHLCV data from 1998-01-02 to 2008-12-31 
    start_date = datetime(1999, 11, 1) 
    end_date = datetime(2022, 12, 31)
    print("Obtaining Apple data from AlphaVantage and saving as CSV...") 
    aapl = av.get_daily_historic_data('AAPL', start_date, end_date) 
    aapl.to_csv("./data/AAPL.csv", index=True)
    symbol_list = ['AAPL']
    csv_dir = '/Users/nymath/quant/trading_systems/data'
    events = queue.Queue()
    # 关于datahandler和portfolio的联合测试
    ## aa
    aa = HistoricCSVDataHandler(events, csv_dir, symbol_list, start_date, end_date)
    dir(aa)
    aa.symbol_list
    aa.symbol_data
    aa.latest_symbol_data 
    aa.update_bars()
    aa.latest_symbol_data['AAPL'][0][1]
    aa.get_latest_bar_value('AAPL', 'close')
    aa.get_latest_bars_values('AAPL', 'close', N=50) # array
    aa.get_latest_bars('AAPL', N=2) # 
    aa.get_latest_bar_datetime('AAPL')
    ## bb
    bb = Portfolio(aa, events, start_date)
    bb.current_positions.keys()
    bb.current_positions.values()
    bb.current_holdings.keys()
    bb.current_holdings.values()
    bb.all_positions
    bb.update_timeindex(MarketEvent())
    
    ## 回顾一下Backtest的流程, 首先来到时刻1, 更新一个bar(这个bar的时间是时刻0)与此同时放入一个MarketEvent()进入队列.
    ## 接着Strategy产生作用, 往队列中放入SignalEvent()与此同时更新仓位(这时候仓位为0, 要等FillEvent到达之后才会更新具体仓位)