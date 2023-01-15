class Event(object):
    """
    Event is base class providing an interface for all subsequent(inherited) events, 
    that will trigger urther eents in the trading infrasturcture.
    """
    pass


# DataHandler generates marketevents
class MarketEvent(Event):
    """
    Handles the event of receiving a new market update with corresponding bars.
    """
    
    def __init__(self):
        """
        Initialises the MarketEvent.
        """
        self.type = 'MARKET'
# strategy processes marketevents and generates signalevents
class SignalEvent(Event):
    """
    Handles the event of sending a Signal froom a Strategy object.
    This is received by a Portfolio object and acted upon.
    """
    
    def __init__(self, strategy_id, symbol, datetime, signal_type, strength):
        """
        strategy_id: The unique identifier for the strategy that generated the signal.
        symbol: 比如股票代码
        datetime: the timestamp at which the signal was generatd.
        signal_type: 'LONG' or 'SHORT'
        strength: An adjustment factor "suggestion" used to scale quantity at the portfolio level. Useful for pairs strategies.
        相当于是策略的权重
        """
        
        self.type = 'SIGNAL'
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength
        
# portfolio class receives a signalevent and translates it to a order event

class OrderEvent(Event):
    """
    Handles the event of sending an Order to an execution system.
    The order contains a symbol, a type, quantity and a direction.
    """
    def __init__(self, symbol, order_type, quantity, direction):
        """
        Initialises the order type, setting whether it is a Market order or Limit order,
        has a quantity and ites diretion.
        Parameters:
        symbol: 股票代码
        order_type: 市价单或者限价单
        quantity: 下单的数量
        direction: "BUY" or "SELL" for long or short
        """
        self.type = "ORDER"
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction
        
    def _check_set_quantity_positive(self, quantity):
        """
        Checks taht quantity is a positive integer.
        """
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("quantity must be a positive integer")
        return quantity
    
    def print_order(self):
        """
        Outputs the values within the Order.
        """
        print(
            f"Order: Symbols={self.symbol}, Type={self.order_type}, Quantity={self.quantity}, Direction={self.direction}"
        )
        
# 有了订单事件，把它传给ExecutionHander，就可以得到fillevent

class FillEvent(Event):
    """
    Encapsulates(压缩) the notion of a FIlled Order, as returned from a brokerage.
    Stores the quantity of an insturment actually filled and at wat price. In addition, stores the commision of the trade from the brokerage.
    """
    def __init__(self, timeindex, symbol, exchange, quantity, direction, fill_cost, commission=None):
        """
        Parameters:
        timeindex: The bar-resolution when the order was filled.
        symbol:
        exchange: 交易所
        quantity: 数量
        direction: 
        fill_cost:
        commission:
        """
        
        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
    
        if commission is None:
            self.commission = self.calculate_ib_commission()
        else:
            self.commission = commission
            
    def calculate_ib_commission(self):
        full_cost = 1.3
        if self.quantity <= 500:
            full_cost = max(1.3, 0.013 * self.quantity)
        else:
            full_cost = max(1.3, 0.008 * self.quantity)
        return full_cost
    