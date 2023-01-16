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

import statsmodels.api as sm


"""
1. Long hte market and below the negative 
"""

class IntradayOLSMRStrategy(strategy):
    """
    Uses ordinary least squares (OLS) to perform a rolling linear regresssion to determine the hedge ratio
    between a pair of equities. The z-score of the residuals time series is then calculated in a rolling
    fashion and if it exceeds an interval of thresolds. (defaulting to [0.5, 3.0]) then a long/short signal air 
    are generated for the high threshold or an exit signal pair are generated (for the low threshold).
    """
    def __init__(self, bars, account, events, ols_window=100,
                 zcore_low=0.5, zscore_high=3.0):
        """
        Initialises the stat arb strategy.
        
        Parameters
        ----------
        bars : HistoricCSVDataHandler
        account : Portfolio
        events: The Event Queue object.
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.account = account
        self.events = events
        self.ols_window = ols_windows
        self.zscore_low = zscore_low
        self.zscore_high = zscore_high

        self.pair = ('AREX', 'WLL')
        self.datetime = datetime.utcnow()
        
        self.long_market = False
        self.short_market = False
        
        
    def calculate_xy_signals(self, zscore_last):
        """
        Calculates the actual x,y signal parings 
        to be sent to the signal generator.
        
        Parameters
        ----------
        zscore_last : The current zscore to test against
        """
        y_signal = None
        x_signal = None
        p0 = self.pair[0]
        p1 = self.pair[1]
        cur_dt = self.datetime
        hr = abs(self.hedge_ratio)
        # 当残差
        if zscore_last <= -self.zscore_high and not self.long_market:
            self.long_market = True
            y_signal = SignalEvent(1, p0, cur_dt, 'LONG', 1.0)
            x_signal = SignalEvent(1, p1, cur_dt, 'SHORT', hr)
        # If we're long the market and between the absolute value of the low zscore threshold
        
        if abs(zscore_last) <= self.zscore_low and self.long_market:
            self.long_market = False
            y_signal = SignalEvent(1, p0, cur_dt, 'EXIT', 1.0)
            x_signal = SignalEvent(1, p1, cur_dt, 'EXIT', 1.0)
            
        # If we're short the market and above the high zscore threshold
        if zscore_last >= self.zscore_high and not self.short_market:
            self.short_market = True
            y_signal = SignalEvent(1, p0, cur_dt, 'SHORT', 1.0)
            x_signal = SignalEvent(1, p1, cur_dt, 'LONG', hr)
        
        # If we're short the market and above the high zscore threshold
        if zscore_last >= self.zscore_high and not self.short_market:
            self.short_market = True
            y_signal = SignalEvent(1, p0, cur_dt, 'SHORT', 1.0)
            x_signal = SignalEvent(1, p1, cur_dt, 'LONG', hr)
        
        # If we're short the market and between the absolute value of 
        # the low zscore threshold
        if abs(zscore_last) <= self.zscore_low and self.short_market:
            self.short_market = False
            y_signal = SignalEvent(1, p0, cur_dt, 'EXIT', 1.0)
            x_signal = SignalEvent(1, p1, cur_dt, 'EXIT', 1.0)
        
        return y_signal, x_signal
            
    def calculate_signals_for_pairs(self):
        """
        Generates a new set of signals based on teh mean reversion strategu.
        
        Calculates the hedge ratio between the pair of tickers.
        We use OLS for this, although we could use CADF.
        """
        # Obtain the latest window of values for each
        # component of the pair of tickers
        y = self.bars.get_latest_bars_values(self.pair[0], 'close', N=self.ols_window)
        x = self.bars.get_latest_bars_values(self.pair[1], 'close', N=self.ols_window)
        
        if y is not None and x is not None:
            # Check that all window periods are available.
            if len(y) >= self.ols_window and len(x) >= self.ols_window:
                # Calculate the current hedge ratio using OLS
                self.hedge_ratio = sm.OLS(y,x).fit().params[0]
                
                # Calculate the current z-score of the residuals
                spread = y - self.hedge_ratio * x
                zscore_last = ((spread - spread.mean()) / spread.std())[-1]
                
                # Calculate signals and add to events queue
                y_signal, x_signal = self.calculate_xy_signals(zscore_last)
                if y_signal is not None and x_signal is not None:
                    self.events.put(y_signal)
                    self.events.put(x_signal)
    
    def calculate_signals(self, event):
        """
        Calculate the SignalEvents based on market data.
        """
        if event.type == 'MARKET':
            self.calculate_signals_for_pairs()
                
                
                
                