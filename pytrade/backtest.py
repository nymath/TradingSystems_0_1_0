import datetime

try:
    import Queue as queue
except ImportError:
    import queue
import time

class Backtest(object):
    """
    Enscapsulates the settings and components for carying out 
    an event-driven backtest.
    """
    
    def __init__(self, csv_dir, symbol_list, initial_capital,
                 heartbeat, start_date, end_date, data_handler, execution_handler,
                 portfolio, strategy):
        """
        Initialises the backtest.
        
        Parameters
        ----------
        csv_dir : The hard root to the CSV data directory.
        symbol_list: 
        initial_capital:
        heartbeat: 
        start_date : 
        data_handler : DataHandler Class
        execution_handler: Class
        portfolio: Portfolio Class
        """
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date
        self.end_date = end_date
        
        self.data_handler_cls = data_handler
        self.strategy_cls = strategy
        self.portfolio_cls = portfolio
        self.execution_handler_cls = execution_handler
        
        self.events = queue.Queue()
        
        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strats = 1 #TODO: 修改策略数量
        
        self._generate_trading_instances()
        
        
    def _generate_trading_instances(self):
        """
        Generates the trading instance objects from their class types
        """
        print("Creating DataHandler, Strategy, Portfolio and ExecutionHandler")
        self.data_handler = self.data_handler_cls(self.events, self.csv_dir, self.symbol_list, self.start_date, self.end_date)
        self.portfolio = self.portfolio_cls(self.data_handler, self.events, self.start_date, self.initial_capital)
        self.execution_handler = self.execution_handler_cls(self.events) 
        self.strategy = self.strategy_cls(self.data_handler, self.portfolio, self.events)
        
    def _run_backtest(self):
        
        i = 0
        while True:
            i += 1
            print(i)
            # Update the market bars
            if self.data_handler.continue_backtest == True:
                self.data_handler.update_bars() # MARK: 更新bar, 放入MarketEvent, 需要值得注意的是, 在取完数据后, 整体还需要运行一次,才会出现continue_backtest
                # == False, 因此会出现两次最后一天，但这个没有问题，因为第一个最后一天计算的是期初的价值, 第二个最后一天计算的是期末的价值(因为通过fillEvent更新的数据)
                # 需要在第二次运行时才会体现.
            else:
                break
            # Handle the events
            # 注意这个while循环，表示一个bar内的操作。当loop1只执行一个MarketEvent, 然后放入SignalEvent, loop2就会开始这行这些SignalEvent，然后...
            while True:
                try:
                    event = self.events.get(False) 
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            self.strategy.calculate_signals(event) #MARK: 放入SignalEvent
                            self.portfolio.update_timeindex(event) # append当前的holdings
                        
                        elif event.type == 'SIGNAL':
                            self.signals += 1
                            self.portfolio.update_signal(event) #MARK: 放入OrderEvent
                            
                        elif event.type == 'ORDER':
                            self.orders += 1 
                            self.execution_handler.execute_order(event) #MARK 放入FillEvent

                        elif event.type == 'FILL':
                            self.fills += 1
                            self.portfolio.update_fill(event) # 因为市值是估计的期末的价值。
                            
            time.sleep(self.heartbeat) # 休息一下
            
    def _output_performance(self):
        """
        Outputs the strategy performance from the backtest.
        """
        self.portfolio.create_equity_curve_dataframe()
        
        print("Creating summary stats ... ")
        stats = self.portfolio.output_summary_stats()
        print("Creating equity curve ...")
        print(self.data_handler.latest_symbol_data['AAPL'][-1:])
        print(self.portfolio.equity_curve.head(10))
        print(self.portfolio.equity_curve.tail(10))
        print(stats)
        print("Signals: %s" % self.signals) 
        print("Orders: %s" % self.orders) 
        print("Fills: %s" % self.fills)
        
    def simulate_trading(self):
        """
        Simulates the backtest and outputs portfolio performance.
        """
        self._run_backtest()
        self._output_performance()
        
    
