import datetime
import time

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

        print(wind_order)
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
        self.positions[None] = Position(0, 0)
        self.sync_position()



    def sync_position(self):
        result = self._store.position_query()
        if len(result.Data) == 3:
            return 0, 0
        trade_side = result.Data[4]
        positions = result.Data[6]
        trade_price = result.Data[2]
        position_size = 0
        position_price = 0
        total_value = 0
        for i in range(len(trade_side)):
            if trade_side[i] == "Buy":
                position_size += positions[i]
                total_value += trade_price[i] * positions[i]
            elif trade_side[i] == "Short":
                position_size -= positions[i]
                total_value -= trade_price[i] * positions[i]
        
        position_price = total_value / position_size

        pos = self.positions[None]
        pos.update(position_size, position_price)



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
        print("pos updated!", pos)


    
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

        print("order_query", order_ids)
        print("trade_query", trade_ids)

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

        check_order_id_list = list(set(order_dict.keys()) - set(self.order_dict.keys()))
        
        print("check_order_id_list, ", check_order_id_list)
        if len(check_order_id_list) == 1:

            this_order_id = check_order_id_list[0]
            
            if order_dict[this_order_id][0] == "Normal":
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
            elif order_dict[this_order_id][0] == "Invalid":
                this_order_status = ORDER_STATUS_INVALID
            elif order_dict[this_order_id][0] == "Cancelled":
                this_order_status = ORDER_STATUS_CANCELED

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

        order_query = self._store.order_query()
        if order_query.ErrorCode != 0:
            raise('order query failed')
        if  self.open_orders:       
            for o in self.open_orders:
                order_id = o.wind_order[0]
                print("open order iiiiiiiiiiiiiiiiiddddddddddd", order_id)
                if order_id in order_query.Data[0]:
                    idx1 = order_query.Data[0].index(order_id)
                    order_status1 = order_query.Data[1][idx1]
                    print("open order sssssssssssstaaaaaaaaaaaaattttttuuuuuussssss", order_status1)
                    if order_status1 in [ORDER_STATUS_CANCELED, ORDER_STATUS_INVALID]:
                        self._set_order_status(o, order_status1)
                        self.open_orders.remove(o)
                        self.notify(o)
                        continue
                print("open trade iiiiiiiiiiddddddddddddddddssssssss", trade_query.Data[0])
                
                if order_id in trade_query.Data[0]:
                    idx2 = trade_query.Data[0].index(order_id)
                    order_status2 = trade_query.Data[2][idx2]
                    
                    if order_status2 == "Normal":
                        order_status2 = ORDER_STATUS_FILLED
                        trade_price =  trade_query.Data[trade_query.Fields.index("TradedPrice")][idx2]
                        trade_size = trade_query.Data[trade_query.Fields.index("TradedVolume")][idx2]
                        trade_time = trade_query.Data[trade_query.Fields.index("TradedTime")][idx2]
                        self._set_order_status(o, order_status2)
                        self._execute_order(o, trade_time, trade_size, trade_price)
                    elif order_status2 == "Invalid":
                        order_status2 = ORDER_STATUS_INVALID
                        self._set_order_status(o, order_status2)
                    elif order_status2 == "Canceled":
                        order_status2 = ORDER_STATUS_CANCELED
                        self._set_order_status(o, order_status2)
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
        print("wind_order:", wind_order)
        if wind_order[0]:
            order = WindOrder(owner, data, exectype, wind_order)
            if wind_order[1] in [ORDER_STATUS_FILLED]:
                self._execute_order(
                    order,
                    wind_order[5],
                    wind_order[4],
                    wind_order[3])
            
  
            self._set_order_status(order, wind_order[1])
            print("popip status ",order.status, Order.Submitted)
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
        print("removeeeeeeeeeeeeeeeee", order_id)
        return self._store.cancel_order(order_id)

    def cancel_open_orders(self):
        for o in self.open_orders:
            self.cancel(o)
            self.open_orders.remove(o)

        
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

