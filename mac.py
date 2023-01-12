
from datetime import datetime

import numpy as np

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from date import HistoricCSVDataHandler
from execution import SimulatedExecutionHandler
from portfolio import Portfolio

class MovingAverageCrossStrategy(Strategy):
    """
    Carries out a asic Moving Average Crossover strategy with a short/long siple weighted moving 
    average. Default short/long windows are 100/400 periods periods respectively.
    """
    def __init__(self, bars, events, short_window=100, long_window=400):
        """
        Initialises the Moving Average Cross Strategy
        
        
        Parameters:
        bars: DataHandler object
        events: The event Queue object.
        short_window = The short moving average lookback
        long_window = The long moving average lookback
        """
        self.bars = bars
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
                bars = self.bars.get_latest_bars_values(s, 'adj_close', N = self.long_window)
                bar_date = self.bars.get_latest_bar_datetime(s)
                if bars is not None and bars != []:
                    short_sma = np.mean(bars[-self.short_window:])
                    long_sma = np.mean(bars[-self.long_window:])
                    
                    symbol = s
                    cur_date = datetime.utcnow()
                    sig_dir = ""
                    
                    # 只有当条件满足时才会产生信号, 
                    if short_sma > long_sma and self.bought[symbol] == "OUT":
                        print("LONG: %s" % bar_date)
                        sig_dir = 'LONG'
                        signal = SignalEvent(1, symbol, cur_date, sig_dir, 1.0)
                        self.events.put(signal) # ------------------ 这里放入了一堆signal-------------------------
                        self.bought[s] = 'LONG'
                        
                    elif short_sma < long_sma and self.bought[symbol] == "LONG":
                        print("SHORT: %s" % bar_date)
                        sig_dir = "EXIT"
                        signal = SignalEvent(strategy_id, symbol, cur_date, sig_dir, 1.0)
                        self.events.put(signal) #  ------------------ 这里放入了一堆signal------------------------
                        self.bought[s] = "OUT"
        