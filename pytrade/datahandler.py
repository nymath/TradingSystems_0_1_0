# 接下来写一些事件算子(从事件到时间的映射)

from abc import ABCMeta, abstractmethod
import datetime
import os, os.path

import numpy as np
import pandas as pd

from .event import MarketEvent

# DataHandler是一个abc, 从而不能够被实例化，但他的子类可以被实例化。 使用__metaclass__ 让python知道这是个abc
# 此外我们也使用@abcstractmethod decorator, 让python知道这个函数会被override


class DataHandler(object):
    """
    DataHandler is an abstract base class providing an interface for all subsequant(inheried) data handlers.
    
    The goal of a Datahndler object is to output a generated set of bars for each symbol requested.
    
    This will replicate how a live strategy would function as current market data would be sent
    "down the pip". Thus a historic and live system will be treated identically by the rest of the backtesting suite. 
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bar(self, symbol):
        """
        Returns the last bar updated.
        """    
        raise NotImplementedError("Should implement get_lateset_bar()")
    
    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars updated.
        """
        raise NotImplementedError("Should implement get_latest_bars()")
    
    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        """
        Returns a Python datetime object for the last bar.
        """
        raise NotImplementedError("Should implement get_latest_datetime()")
    
    @abstractmethod
    def get_latest_bar_value(self, symbol, val_type):
        """
        返回OHLCOI from the last bar.
        """
        raise NotImplementedError("Should implement get_lateset_bar_value()")

    @abstractmethod
    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        Returns the last N bar values from the latest_symbol list or N-k if less available,
        """
        raise NotImplementedError("Should implement get_latest_bars_values()")
    
    @abstractmethod
    def update_bars(self):
        """
        Pushes the lastes bars to the bars_queue for each symbol in a tuple OHLCVI format:
        (datetime, open, high, low, close, volumn, open interest).
        """
        raise NotImplementedError("Should implement update_bars()")
    
    
## 由于没有固定的数据来源, 所以我还是采用csv, 

class HistoricCSVDataHandler(DataHandler):
    """
    读csv文件
    """
    def __init__(self, events, csv_dir, symbol_list, start_date, end_date):
        """
        events: 事件队列
        """
        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.start_date = start_date
        self.end_date = end_date
        
        
        self.symbol_data = {} # 存放所有
        self.latest_symbol_data = {}
        self.continue_backtest = True
        
        self._open_convert_csv_files()
        
        
    def _open_convert_csv_files(self):
        """
        加载csv文件, 并转化为DataFrames 格式
        """
        # 读入历史所有数据，并将第一列作为DatetimeIndex
        # 
        comb_index = None
        
        for s in self.symbol_list:
            self.symbol_data[s] = pd.read_csv(
                os.path.join(self.csv_dir, f'{s}.csv'),
                header=0, index_col=0, parse_dates=True,
                names = [
                    'datetime', 'open', 'high', 'low', 'close', 'volume', 'adj_close',
                ]
            )
            self.symbol_data[s].sort_index(inplace=True)
            self.symbol_data[s] = self.symbol_data[s][self.start_date:self.end_date]
            # Combine the index to pad forward values, 换句话说, 我们后边需要取合并数据集，所以index选择untion
            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index.union(self.symbol_data[s].index)
            # 把最新的数据设置为空
            self.latest_symbol_data[s] = []
            
        for s in self.symbol_list:
            # 更改index, 事实上应该是可以直接用trade_dates
            self.symbol_data[s] = self.symbol_data[s].reindex(
                index = comb_index, method='pad'
            )
            self.symbol_data[s]["returns"] = self.symbol_data[s]["adj_close" ].pct_change().dropna() # 这个dropna感觉没什么用, 返回的结果和你想象的一样
            # 然后按照rows, 把一个股票的行情数据转化为一个generator, 这个generator每次生成一个tuple, 这个tuple的第一个元素是时间
            self.symbol_data[s] = self.symbol_data[s].iterrows()
            
    def _get_new_bar(self, symbol):
        """
        Return the lastest bar from the date feed.
        """
        for b in self.symbol_data[symbol]:
            yield b 
        # 这和直接next(self.symbol_data[symbol])效果一样
    def get_latest_bar(self, symbol):
        """
        Returns the last bar from the lastes_symbol list
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1]
        
    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list,
        or N-k if less available.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-N:]
            
    def get_latest_bar_datetime(self, symbol):
        """
        Returns a Python datime object for the last bar
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1][0]
        
    def get_latest_bar_value(self, symbol, val_type):
        """
        Returns one of the Open, High, Low, Close, Volumn or OI
        values from the Pandas Bar series object.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return getattr(bars_list[-1][1], val_type) # 因为我们知道了bars_list是一个tuple, 第一个位置是一个series
        
    def get_latest_bars_values(self, symbol, val_type, N=1) -> np.array:
        """
        Returns the last N bar values from the 
        latest_symbol list, or N-k if less available
        """
        try:
            bars_list = self.get_latest_bars(symbol, N)
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return np.array([getattr(b[1], val_type) for b in bars_list])
    
    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure
        for all symbols in the self.symbol_list
        """
        for s in self.symbol_list:
            try:
                bar = next(self._get_new_bar(s)) # 取一天的数据, 然后self.symbol_data就少一行数据, 而且这和直接next(self.symbol_data[symbol])效果一样
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
        self.events.put(MarketEvent())

