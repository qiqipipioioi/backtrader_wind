import time

from functools import wraps
from math import floor

from backtrader.dataseries import TimeFrame
from requests.exceptions import ConnectTimeout, ConnectionError

from .windbroker import WindBroker
from .winddata import WindData

from WindPy import *


class WindStore(object):


    def __init__(self, logonAccount, password, accountType, target, testnet=False, retries=5):

        self.w = w
        self.w.start()

        self.brokerID = "0000"
        self.departmentID = 0
        self.logonAccount = logonAccount
        self.password = password
        self.accountType = accountType

        self.logon = self.w.tlogon(BrokerID = self.brokerID, DepartmentID = self.departmentID, \
                              LogonAccount = self.logonAccount, Password = self.password, AccountType = self.accountType)

        if self.logon.ErrorCode == 0:
            print("logon success!")
        else:
            print(self.logon)
            raise

        self.symbol = target
        #self.retries = retries

        self._cash = 0
        self._value = 0
        self.get_balance()

        #self._step_size = None
        #self._tick_size = None
        #self.get_filters()

        self._broker = WindBroker(store=self)
        self._data = None

    def retry(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            for attempt in range(1, self.retries + 1):
                time.sleep(0.1)
                result = func(self, *args, **kwargs)
                if result.ErrorCode == 0:
                    return result
                if attempt == self.retries:
                    raise ConnectionError("connect error")

    
    def cancel_open_orders(self):
        orders = self.windbroker.get_open_orders(symbol=self.symbol)
        if len(orders) > 0:
            for o in orders:
                id = o.windorder[0]
                self.cancel_order(id)

    @retry
    def cancel_order(self, order_id):
        self.w.tcancel(OrderNumber = order_id)

    
    @retry
    def create_order(self, side, type, size, price):
        print(self.symbol, side, price, size)
        return self.w.torder(SecurityCode = self.symbol, TradeSide = side, OrderPrice = price, \
                             OrderVolume = size)

    def format_price(self, price):
        return self._format_value(price, self._tick_size)
    
    def format_quantity(self, size):
        return self._format_value(size, self._step_size)

    @retry
    def get_asset_balance(self):
        capital = self.w.tquery('Capital')
        print(capital.Data)
        free = capital.Data[1][0]
        locked = capital.Data[4][0]
        balance = {'free': free, 'locked': locked}
        
        return float(balance['free']), float(balance['locked'])

    def get_balance(self):
        free, locked = self.get_asset_balance()
        self._cash = free
        self._value = free + locked

    def getbroker(self):
        return self._broker

    def getdata(self, timeframe_in_minutes, start_date=None):
        if not self._data:
            self._data = WindData(store=self, timeframe_in_minutes=timeframe_in_minutes, start_date=start_date)
        return self._data

    def get_realtime_data(self, symbol):
        return self.w.wsq(codes = symbol, fields ='rt_open, rt_high, rt_low, rt_last, rt_last_vol')
    
    def get_history_data(self, symbol, start_date):
        return self.w.wsi(codes = symbol, fields = "open, high, low, close, volume", beginTime = start_date)
        
    # def get_filters(self):
    #     symbol_info = self.get_symbol_info(self.symbol)
    #     for f in symbol_info['filters']:
    #         if f['filterType'] == 'LOT_SIZE':
    #             self._step_size = f['stepSize']
    #         elif f['filterType'] == 'PRICE_FILTER':
    #             self._tick_size = f['tickSize']

    # def get_interval(self, timeframe, compression):
    #     return self._GRANULARITIES.get((timeframe, compression))

    @retry
    def get_symbol_info(self, symbol):
        return symbol

    def order_query(self):
        import time
        time.sleep(0.1)
        return self.w.tquery('Order')

    def trade_query(self):
        import time
        time.sleep(0.1)
        return self.w.tquery('Trade')

    def stop_socket(self):
        self.w.logout()
        self.w.stop()
