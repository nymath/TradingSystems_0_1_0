import datetime
from math import floor

try:
    import Queue as queue
except ImportError:
    import queue
    
import numpy as np
import pandas as pd

from .event import FillEvent, OrderEvent
from .performance import create_sharpe_ratio, create_drawdowns

class Portfolio(object):
    """
    The Portfolio class handles hte positions and market value of all instruments at a resolution
    of a "bar".
    
    The positions DataFrame stores a time-index of the quantity of positions held.
    The holdings DataFrame stores the cash and total market holdings value of each symbo for a particular
    time-idnex, as well as the percentage change in portfolio total across bars.
    """
    def __init__(self, bars, events, start_date, initial_capital = 100000.0):
        """
        Initialises the portfolio with bars and an event queue.
        Also includes a starting datetime index and initial capital
        
        Parameters:
        bars: The DataHandler object with current market data, 就是我们的DataHandler对象
        
        events: The Event Queue object, 因为portfolio会往事件队列中put一些OrderEvent以及FillEvetn
        
        start_date: The start date of the portfolio.
        
        initial_capital: The starting capital.
        """
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital
        
        self.all_positions = self.construct_all_positions()
        self.current_positions = dict( (k,v) for k,v in [(s,0) for s in self.symbol_list])
        
        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()
        
    def construct_all_positions(self):
        """
        constructs the positions list using the start_date
        to determine when the time index will begin.
        """
        d = dict( (k,v) for k,v in [(s,0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        return [d]
    
    def construct_all_holdings(self):
        """
        Constructs the holdings list using the start_date
        to determine when the time index will begin.
        """
        d = dict( (k,v)  for k,v in [(s,0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]
        
    def construct_current_holdings(self):
        """
        This contructs the dictionary which will hold the instantaneous value of 
        the portfolio arcoss all symbols.
        """
        d = dict( (k,v) for k,v in [(s,0) for s in self.symbol_list])
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d
    
    def update_timeindex(self, event): # 似乎event参数没有使用
        """
        Adds a new record to the positions martrix for the current market data bar.
        This reflects the PREVIOUS bar
        
        Makes use of a MarketEvent from the events queue.
        """
        latest_datetime = self.bars.get_latest_bar_datetime(self.symbol_list[0])
        
        # update positions
        # =================
        dp = dict( (k,v) for k,v in [(s,0) for s in self.symbol_list])
        dp['datetime'] = latest_datetime
        
        for s in self.symbol_list:
            dp[s] = self.current_positions[s]
        # Append the current positions
        self.all_positions.append(dp)
        
        # Update holdings
        # ================
        dh = dict( (k,v) for k,v in [(s,0) for s in self.symbol_list])
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']
        
        for s in self.symbol_list:
            # Approximation to the real value
            market_value = self.current_positions[s] * self.bars.get_latest_bar_value(s, 'adj_close')
        
            dh[s] = market_value
            dh['total'] += market_value
            
        # Append the current holdings
        self.all_holdings.append(dh)
        
    def update_positions_from_fill(self, fill):
        """

        Takes a Fill object and updates the position matrix to reflect the new position
        
        Parameters:
        fill: The Fill object to update the positions with.
        """
        # Check whether the fill is a buy or sell
        fill_dir = 0
        if fill.direction == "BUY":
            fill_dir = 1
        if fill.direction == "SELL":
            fill_dir = -1
        
        # Update positions list with new quantities
        self.current_positions[fill.symbol] += fill_dir*fill.quantity
    
    def update_holdings_from_fill(self, fill):
        """
        Takes a Fill object and updates the holdings matrix to 
        reflect the holdings value.
        
        Parameters:
        fill: The Fill object to update the holdings with.
        """
        # check whether the fill is a buy orsell
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == "SELL":
            fill_dir = -1
            
        # Update holdings list with new quantities
        fill_cost = self.bars.get_latest_bar_value(fill.symbol, "adj_close")
        cost = fill_dir * fill_cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= (cost + fill.commission)
    
    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings
        from a FillEvent
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)
            
    def generate_naive_order(self, signal):
        """
        Simple files on Order object as a constant quantity sizing of the signal object, without risk management or position sizing considerations.
        
        Parameters:
        signal: The tuple containing Signal information
        """
        order = None
        
        symbol = signal.symbol
        direction = signal.signal_type
        strength = signal.strength
        
        mkt_quantity = 100
        cur_quantity = self.current_positions[symbol]
        order_type = 'MKT'
        
        if direction == 'LONG' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
        if direction == 'SHORT' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')
            
        if direction == 'EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
        if direction == 'EXIT' and cur_quantity < 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY')
        return order
    
    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new orders
        based on the portfolio logic
        """
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)  #MARK: 放入信号事件 

    def create_equity_curve_dataframe(self):
        """
        Creates a Pandas DataFrame from all_holdings list of dictionaries.
        """
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace = True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1+curve['returns']).cumprod()
        self.equity_curve = curve
        
    def output_summary_stats(self):
        """
        Create a list of summary statsitics for the portfolio.
        """
        total_return = self.equity_curve['equity_curve'][-1]
        returns = self.equity_curve['returns']
        pnl = self.equity_curve['equity_curve'] 
        
        sharpe_ratio = create_sharpe_ratio(returns,periods=252) #FIXME: 修改时间频率
        drawdown, max_dd, dd_duration = create_drawdowns(pnl)
        self.equity_curve['drawdown'] = drawdown
        
        stats = [("Total Return", "%0.2f%%" % ((total_return - 1.0) * 100.0)), 
                 ("Sharpe Ratio", "%0.2f" % sharpe_ratio), 
                 ("Max Drawdown", "%0.2f%%" % (max_dd * 100.0)), 
                 ("Drawdown Duration", "%d" % dd_duration)]
        self.equity_curve.to_csv('equity.csv')
        return stats
    
    

        