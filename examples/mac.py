from datetime import datetime 
import os 
import sys 
sys.path.append(os.getcwd())
import pandas as pd
import numpy as np
from alpha_vantage import AlphaVantage
import queue

from pytrade.strategy import Strategy
from pytrade.event import SignalEvent
from pytrade.backtest import Backtest
from pytrade.datahandler import HistoricCSVDataHandler
from pytrade.execution import SimulatedExecutionHandler
from pytrade.portfolio import Portfolio

# Entry signals are only generated if the attribute bought is "Out", and exit signals are only ever generated if this is "LONG"
# or "SHORT".
# 简单均线策略, 短均线上穿长均线时, 用百分之80的现金购买股票, 
# 短均线下穿长均线时, 清空手里的头寸，直到下一个信号出现.

## 策略总结
## 在20010928发生了一次极大的回撤, 苹果公司的股价发生了, 可以试试改变长短期均线长度, 试试能否避免这次回撤。

class MovingAverageCrossStrategy(Strategy):
    """
    Carries out a asic Moving Average Crossover strategy with a short/long siple weighted moving 
    average. Default short/long windows are 100/400 periods periods respectively.
    """
    def __init__(self, bars, account, events, short_window=50, long_window=200):
        """
        Initialises the Moving Average Cross Strategy
        
        Parameters:
        ----------------------------------
        bars: DataHandler object
        events: The event Queue object.
        short_window = The short moving average lookback
        long_window = The long moving average lookback
        """
        self.bars = bars
        self.account = account
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.short_window = short_window
        self.long_window = long_window
        
        # Set to True if a symbol is in the market
        self.bought = self._calculate_initial_bought()
        
    def _calculate_initial_bought(self):
        """
        Adds keys to the bought dicionary for all symbols
        and sets them to "OUT"
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = "OUT" # 有LONG以及OUT两种
        return bought
    
    def calculate_signals(self, event):
        """
        Generates a new set of signals based on the MACSMA with the short window crossing the long
        window meaning a long entry and vice versa for a short entry.
        Parameters:
        event: A MarketEvent object
        """
        if event.type == "MARKET":
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars_values(s, 'adj_close', N = self.long_window) # array
                bar_date = self.bars.get_latest_bar_datetime(s)
                if  bars is not None: #TODO 修改判定方式
                    short_sma = np.mean(bars[-self.short_window:])
                    long_sma = np.mean(bars[-self.long_window:])
                    
                    symbol = s
                    cur_date = datetime.utcnow()
                    sig_dir = ""
                    # 只有当条件满足时才会产生信号, 
                    if short_sma > long_sma and self.bought[symbol] == "OUT":
                        print("LONG: %s" % bar_date)
                        sig_dir = 'LONG'
                        cash = self.account.current_holdings['cash'] # 注意是我们是以昨天的收盘价成交的
                        price = self.bars.get_latest_bar_value(s, 'adj_close')
                        n = int(0.8 * cash / price / 100)
                        signal = SignalEvent(1, symbol, cur_date, sig_dir, 1.0) # 一手
                        for i in range(n):
                            self.events.put(signal)
                        self.bought[s] = 'LONG'
                        
                    elif short_sma < long_sma and self.bought[symbol] == "LONG":
                        print("SHORT: %s" % bar_date)
                        sig_dir = "EXIT"
                        signal = SignalEvent(1, symbol, cur_date, sig_dir, 1.0)
                        self.events.put(signal) 
                        self.bought[s] = "OUT"

def order_target():
    pass



if __name__ == "__main__":
    # 获取数据
    av = AlphaVantage()
    start_date = datetime(1998, 1, 2)
    end_date = datetime(2008, 12, 31)
    print("Obtaining Apple data from AlphaVantage and saving as CSV...") 
    aapl = av.get_daily_historic_data('AAPL', start_date, end_date) 
    aapl.to_csv("./data/AAPL.csv", index=True)
    
    # 开始回测
    csv_dir = './data'
    symbol_list = ['AAPL']
    initial_capital = 100000.0
    heartbeat = 0.0
    
    backtest = Backtest(csv_dir, symbol_list, initial_capital, heartbeat, start_date, end_date,
                        HistoricCSVDataHandler, 
                        SimulatedExecutionHandler,
                        Portfolio, 
                        MovingAverageCrossStrategy)
    backtest.simulate_trading()
    