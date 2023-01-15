import datetime

import time
import os
import sys
sys.path.append(os.getcwd())
from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import ibConnection, message

from pytrade.event import FillEvent, OrderEvent
from pytrade.execution import ExecutionHandler

class IBexecutionHandler(ExecutionHandler()):
    """
    Handles order execution via the Interactive Brokers API, 
    for use against accounts when trading live directyly.
    """
    def __init__(self, events, order_routing="SMART", currency = "USD"):
        """
        Initialises the IBExecutionHandler instance.
        """
        self.events = events
        self.order_routing = order_routing
        self.currency = currency
        self.fill_dict = {}
        self.tws_conn = self.create_tws_connection()
        self.order_id = self.create_initial_order_id()
        self.register_handlers()
        
    def _error_handler(self, msg):
        """
        Handles the capturing of error messages 
        """
        # Cureently no error handling.
        print(f"Server Error: {msg}")
    
    def _reply_handler(self, msg):
        """
        Handles of server replies
        """
        # Handle open order orderId processing
        if msg.typeName == "openOrder" and \
            msg.orderId == self.order_id and \
            not self.flll_dict.has_key(msg.orderId):
                self.create_fill_dict_entry(msg)
        # Handle fills
        if msg.typeName == 'orderStatus' and \
            msg.status == 'Filled' and \
            self.fill_dict[msg.orderId]['filled'] == False:
            self.create_fill(msg)
        print("Serve Response: %s, %s\n" % (msg.typeName, msg))
    
    def create_tws_connection(self):
        """
        Connect to hte Trader Workstation(TWS) runnign on the usual port of 7496, with a clientID of 10.
        The clientId is chosen by us and we will need separate IDs for both the exectuion connection and market data connection, 
        if the latter is used elsewhere.
        """
        tws_conn = ibConnection()
        tws_conn.connect()
        return tws_conn
    
    def create_initial_order_id(self):
        """
        Creates the initial order ID used for Interactive 
        Brokers to keep track of submitted orders.
        """
        # There is scope for more logic here, but
        # we will use "1" as the default for now.
        return 1
    
    def register_handlers(self):
        """
        Register the error and server reply message handling functions.
        """
        # Assign the error handling function defined above to the TWS connection
        self.tws_conn.register(self._error_handler(msg), 'Error')
        
        # Assign all of the server reply messages to the reply_handler function defined above
        self.tws_conn.registerAll(self._reply_handler)
        
    def create_contract(self, symbol, sec_type, exch, prim_exch, curr):
        """
        Create a Contract object definig what will be purchased, at which exchange and in which currency.
        """
        contract = Contract()
        contract.m_symbol = symbol
        contract.m_secType = sec_type
        contract.m_exchange = exch
        contract.m_primaryExch = prim_exch
        contract.m_currency = curr
        return contract
    
    def create_order(self, order_type, quantity, action):
        """
        Create an Order object (Market/Limit) to go long/short
        """
        order = Order()
        order.m_orderType = order_type
        order.m_totalQuantity = quantity
        order.m_action = action
        return order
    
    def create_fill_dict_entry(self, msg):
        """
        Creates an entry in the Fill Dictionary that lists
        orderIds and provides security information. This is needed for the event-driven behaviour of the IB server message 
        behaviour.
        """
        

            