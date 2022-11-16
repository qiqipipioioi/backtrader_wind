import datetime

from collections import defaultdict, deque
from math import copysign

from backtrader.broker import BrokerBase
from backtrader.order import Order, OrderBase
from backtrader.position import Position


ORDER_STATUS_SUBMITIED = "Submit"
ORDER_STATUS_FILLED = "Filled"
ORDER_STATUS_CANCELED = "Cancelled"
ORDER_STATUS_INVALID = "Invalid"



class WindOrder(OrderBase):
    def __init__(self, owner, data, exectype, wind_order):
        order_types = ["Buy", "Sell"]

        self.owner = owner
        self.data = data
        self.exectype = exectype

        wind_order_status = wind_order[2]
        if wind_order_status == "Short":
            wind_order_status = "Sell"
        elif wind_order_status == "Cover":
            wind_order_status = "Buy"

        self.ordtype = order_types.index(wind_order_status)
        
        
        self.price = float(wind_order[3])
        self.size = int(wind_order[4])
        self.dt = wind_order[5]
        self.wind_order = wind_order
        
        super(WindOrder, self).__init__()
        #self.accept()


class WindBroker(BrokerBase):

    def __init__(self, store):
        super(WindBroker, self).__init__()

        self.notifs = deque()
        self.positions = defaultdict(Position)

        self.open_orders = list()
    
        self._store = store

        #order init
        order_query = self._store.order_query()
        if order_query.ErrorCode != 0:
            raise('trade query failed')
        
        order_ids = order_query.Data[0]

        self.order_dict = {}
        if len(order_query.Data) > 3:
            for i in range(len(order_ids)):
                order_id = order_ids[i]
                order_status = order_query.Data[1][i]
                order_side = order_query.Data[4][i]
                order_price = order_query.Data[5][i]
                order_size = order_query.Data[6][i]
                order_time = order_query.Data[7][i]
                if order_id:
                    self.order_dict[order_id] = [order_status, order_side, order_price, order_size, order_time]

        #postion init
        size, price = self.get_position()
        self.positions[None] = Position(size, price)


    def get_position(self):
        result = self._store.position_query()
        if len(result.Data) == 3:
            return 0, 0
        trade_side = result.Data[4]
        positions = result.Data[6]
        trade_price = result.Data[2]
        position_size = 0
        position_price = 0
        for i in range(len(trade_side)):
            if trade_side[i] == "Buy":
                position_size += positions[i]
            elif trade_side[i] == "Short":
                position_size -= positions[i]
        if len(trade_price) > 1:
            if position_size > 0 :
                position_price = trade_price[0]
            elif position_size < 0:
                position_price = trade_price[1]
        else:
            position_price = trade_price[0]

        return position_size, position_price


    def getposition(self, data, clone=True):
        pos = self.positions[data._dataname]
        if clone:
            pos = pos.clone()
        return pos


    def _execute_order(self, order, date, executed_size, executed_price):
        order.execute(
            date,
            executed_size,
            executed_price,
            0, 0.0, 0.0,
            0, 0.0, 0.0,
            0.0, 0.0,
            0, 0.0)
        pos = self.getposition(order.data, clone = False)
        pos.update(copysign(executed_size, order.size), executed_price)
        print("pos update:", pos)

    
    def _set_order_status(self, order, wind_order_status):
        if wind_order_status == ORDER_STATUS_CANCELED:
            order.cancel()
        elif wind_order_status == ORDER_STATUS_FILLED:
            order.completed()
        elif wind_order_status == ORDER_STATUS_SUBMITIED:
            order.submit()
        elif wind_order_status == ORDER_STATUS_INVALID:
            order.reject()
    
    def _check_order_status(self):
        order_query = self._store.order_query()
        if order_query.ErrorCode != 0:
            raise('order query failed')
        trade_query = self._store.trade_query()
        if trade_query.ErrorCode != 0:
            raise('trade query failed')

        order_ids = order_query.Data[0]
        trade_ids = trade_query.Data[0]

        order_dict = {}
        for i in range(len(order_ids)):
            order_id = order_ids[i]
            order_status = order_query.Data[1][i]
            order_side = order_query.Data[4][i]
            order_price = order_query.Data[5][i]
            order_size = order_query.Data[6][i]
            order_time = order_query.Data[7][i]
            if order_id:
                order_dict[order_id] = [order_status, order_side, order_price, order_size, order_time]
    
        
        this_order_id = None
        this_order_status = ORDER_STATUS_INVALID
        this_order_side = None
        this_order_price = None
        this_order_size = None
        this_order_time = None
        
        if len(order_dict) - len(self.order_dict) == 1:

            this_order_id = list(set(order_dict.keys()) - set(self.order_dict.keys()))[0]
            
            this_order_status = ORDER_STATUS_SUBMITIED
            this_order_side = order_dict[this_order_id][1]
            this_order_price = order_dict[this_order_id][2]
            this_order_size = order_dict[this_order_id][3]
            this_order_time = order_dict[this_order_id][4]
            if this_order_id in trade_ids:
                idx = trade_query.Data[0].index(this_order_id)
                this_trade_status = trade_query.Data[2][idx]
                if this_trade_status == "Normal":
                    this_order_status = ORDER_STATUS_FILLED
                    this_order_price = trade_query.Data[trade_query.Fields.index("TradedPrice")][idx]
                    this_order_size = trade_query.Data[trade_query.Fields.index("TradedVolume")][idx]
                    this_order_time = trade_query.Data[trade_query.Fields.index("TradedTime")][idx]
                elif this_trade_status == "Canceled":
                    this_order_status = ORDER_STATUS_CANCELED
                else:
                    this_order_status = ORDER_STATUS_INVALID

        self.order_dict = order_dict


        return [this_order_id, 
                this_order_status,
                this_order_side, 
                this_order_price, 
                this_order_size, 
                this_order_time]
        

    def check_open_order_status(self):
        trade_query = self._store.trade_query()
        if trade_query.ErrorCode != 0:
            raise('trade query failed')
        if  self.open_orders:       
            for o in self.open_orders:
                order_id = o.wind_order[0]
                if order_id in trade_query.Data[0]:
                    idx = trade_query.Data[0].index(order_id)
                    order_status = trade_query.Data[2][idx]
                    print("here:", order_status)
                    if order_status == "Normal":
                        order_status = ORDER_STATUS_FILLED
                        trade_price =  trade_query.Data[trade_query.Fields.index("TradedPrice")][idx]
                        trade_size = trade_query.Data[trade_query.Fields.index("TradedVolume")][idx]
                        trade_time = trade_query.Data[trade_query.Fields.index("TradedTime")][idx]
                        self._set_order_status(o, order_status)
                        self._execute_order(o, trade_time, trade_size, trade_price)
                    elif order_status == "Invalid":
                        order_status = ORDER_STATUS_INVALID
                        self._set_order_status(o, order_status)
                    elif order_status == "Canceled":
                        order_status = ORDER_STATUS_CANCELED
                        self._set_order_status(o, order_status)
                    self.open_orders.remove(o)
                    self.notify(o)


    def _submit(self, owner, data, side, exectype, size, price):
        #type = self._ORDER_TYPES.get(exectype, ORDER_TYPE_MARKET)

        result = self._store.create_order(side, type, size, price)
        if result.ErrorCode == 0:
            print("order request succeed!")
        else:
            raise("request failed")

        wind_order = self._check_order_status()
        if wind_order[0]:
            order = WindOrder(owner, data, exectype, wind_order)
            if wind_order[1] in [ORDER_STATUS_FILLED]:
                self._execute_order(
                    order,
                    wind_order[5],
                    wind_order[4],
                    wind_order[3])
            
            self._set_order_status(order, wind_order[1])
            if order.status == Order.Submitted:
                self.open_orders.append(order)
            self.notify(order)
            return order

    def buy(self, owner, data, size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None,
            **kwargs):
        print("BBBBBBUUUUUUYYYYY")
        pos = self.positions[None].size
        if pos >= 0:
            side = "Buy"
        else:
            side = "Cover"
        return self._submit(owner, data, side, exectype, size, price)

    def sell(self, owner, data, size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None,
            **kwargs):
        print("SEEEEEEELLLLLLLLL")
        pos = self.positions[None].size
        if pos > 0:
            side = "Sell"
        else:
            side = "Short"
        return self._submit(owner, data, side, exectype, size, price)


    def cancel(self, order):
        order_id = order.wind_order[0]
        return self._store.cancel_order(order_id)

    def cancel_open_orders(self):
        for o in self.open_orders:
            self.cancel(o)
        
    def format_price(self, value):
        return self._store.format_price(value)

    def get_asset_balance(self, asset):
        return self._store.get_asset_balance(asset)

    def getcash(self):
        self.cash = self._store._cash
        return self.cash

    def get_notification(self):
        if not self.notifs:
            return None

        return self.notifs.popleft()



    def getvalue(self, datas=None):
        self.value = self._store._value
        return self.value

    def notify(self, order):
        self.notifs.append(order)

