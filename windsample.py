import datetime
import time

import backtrader as bt
from backtrader.utils import num2date
import backtrader.indicators as btind 

from bt_wind.windstore import WindStore


class RSIStrategy(bt.Strategy):

    params = dict(ma_period_short = 5, ma_period_long = 20)

    def __init__(self):
        self.add_float = 0.01
        self.sma1 = btind.SMA(self.data1.close, period=self.p.ma_period_short)
        self.sma2 = btind.SMA(self.data1.close, period=self.p.ma_period_long)
        self.crossover = btind.CrossOver(self.sma1, self.sma2)
        self.count = 0
        self.ac = 0
        #if self.data.open[0]

    def next(self):
        print('ac:', self.ac)
        self.ac += 1
        print("open orders: ", len(self.broker.open_orders))
        #time.sleep(5)
        print('position', self.position.size)
        print("data len", len(self.data))
        print("data1 len", len(self.data1))
        print("sma1 len", len(self.sma1), self.sma1[0])
        print("sma2 len", len(self.sma2), self.sma2[0])
        print("cross len", len(self.crossover), self.crossover > 0, self.crossover < 0)
        price = self.data.open[0]

        if self.ac <= 200:
            return 


        if self.count > 0:
            self.count -= 1
            return

        if self.crossover[0] > 0:
            if self.position.size == 0:
                self.broker.check_open_order_status()
                self.broker.cancel_open_orders()
                self.buy(data=self.data, size = 1, price = price + self.add_float )
                self.count = 10

            elif self.position.size < 0:
                self.broker.check_open_order_status()
                self.broker.cancel_open_orders()
                self.buy(data=self.data, size = abs(self.position.size), price = price + self.add_float)    
                self.buy(data=self.data, size = 1, price = price + self.add_float)   
                self.count = 10      
            else:
                pass
        elif self.crossover < 0:
            if self.position.size == 0:
                self.broker.check_open_order_status()
                self.broker.cancel_open_orders()
                self.sell(data=self.data, size = 1, price = price - self.add_float) 
                self.count = 10
            elif self.position.size > 0:
                self.broker.check_open_order_status()
                self.broker.cancel_open_orders()
                self.sell(data=self.data, size = abs(self.position.size), price = price - self.add_float)
                self.sell(data=self.data, size = 1, price = price - self.add_float)
                self.count = 10
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
                      target="T2212.CFE")
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
