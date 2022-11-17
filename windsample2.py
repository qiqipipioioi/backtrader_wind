import datetime
import time
from math import copysign

import backtrader as bt
from backtrader.utils import num2date
import backtrader.indicators as btind 

from bt_wind.windstore import WindStore


class RSIStrategy(bt.Strategy):

    params = dict(ma_period_short = 5, ma_period_long = 20)

    def __init__(self):
        self.add_float = 0.005
        self.count = 0
        self.ac = 0

        self.stop_loss = -100
        self.max_profit = 0
        #if self.data.open[0]

    def next(self):


        if self.data._state != 0:
            return 


        if self.count > 0:
            self.count -= 1
            return

        print('ac:', self.ac)
        self.ac += 1
        print("data status,", self.data._state)
        print("open orders: ", len(self.broker.open_orders))

        print('position', self.position.size, self.position.price)
        print("data len", len(self.data))
        print("data1 len", len(self.data1))

        price = self.data.open[0]

        self.broker.check_open_order_status()
        self.broker.cancel_open_orders()

        high = []
        low = []
        for i in range(-9, 0):
            high.append(self.data1.high[i])
            low.append(self.data1.low[i])

        last_10_high = max(high)
        last_10_low = min(low)

        trade_sig = 0

        print('last_10_high:', last_10_high)
        print('last_10_low:', last_10_low)
        print("this price", self.data.close[0])

        if self.data.close[0] > last_10_high:
            trade_sig = 1
        elif self.data.close[0] < last_10_low:
            trade_sig = -1

        if self.position.size != 0:
            now_profit = (self.data.close[0] - self.position.price) * 10000 * self.position.size/ abs(self.position.size)
            if now_profit > 0:
                if now_profit > self.max_profit:
                    self.max_profit = now_profit
                self.stop_loss = self.max_profit - 200
            else:
                self.stop_loss = -200
            print('this trade profit:', now_profit)
        else:
            self.stop_loss = -200
            self.max_profit = 0

        if self.position.size > 0:
            if (self.data.close[0] - self.position.price) * 10000 <= self.stop_loss:
                self.sell(data=self.data, size = abs(self.position.size), price = price - self.add_float)
                self.count = 10
                return
        elif self.position.size < 0 :
            if -(self.data.close[0] - self.position.price) * 10000 <= self.stop_loss:
                self.buy(data=self.data, size = abs(self.position.size), price = price - self.add_float)   
                self.count = 10    
                return    

        if trade_sig > 0:
            if self.position.size == 0:
                self.buy(data=self.data, size = 1, price = price + self.add_float )
                self.count = 10

            # elif self.position.size < 0:
            #     self.buy(data=self.data, size = abs(self.position.size), price = price + self.add_float)    
            #     self.buy(data=self.data, size = 1, price = price + self.add_float)   
            #     self.count = 10      
            else:
                pass
        elif trade_sig < 0:
            if self.position.size == 0:
                self.sell(data=self.data, size = 1, price = price - self.add_float) 
                self.count = 10
            # elif self.position.size > 0:
            #     self.sell(data=self.data, size = abs(self.position.size), price = price - self.add_float)
            #     self.sell(data=self.data, size = 1, price = price - self.add_float)
            #     self.count = 10
            else:
                pass            

    def notify_order(self, order):
        print(order) 

    def notify_trade(self, trade):
        print(trade)                    

        

if __name__ == '__main__':
    cerebro = bt.Cerebro(quicknotify=True)

    store = WindStore(logonAccount="M5Q1V8R2732",
                      password="0",
                      accountType="CFE",
                      target="T2303.CFE")
    broker = store.getbroker()
    cerebro.setbroker(broker)

    from_date = datetime.datetime.utcnow() - datetime.timedelta(minutes=20)
    print(from_date)

    cerebro.addstrategy(RSIStrategy)

    data = store.getdata(
        timeframe_in_minutes=bt.TimeFrame.Ticks,
        start_date=from_date)

    cerebro.adddata(data)

#    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=1)
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Seconds, compression=5)

    cerebro.run()
