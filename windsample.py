import datetime

import backtrader as bt
from backtrader.utils import num2date

from bt_wind.windstore import WindStore


class RSIStrategy(bt.Strategy):
    def __init__(self):
        #self.rsi = bt.indicators.RSI(period=2)  # RSI indicator
        #self.rma = bt.indicators.EMA(period=2)
        self.round = 0
        self.add_float = 0.01

    def next(self):
        print("round:", self.round)
        self.round += 1
        print("data0:", num2date(self.data.datetime[0]), self.data.open[0], self.data.high[0], self.data.low[0], self.data.close[0])
        print("data1:", num2date(self.data1.datetime[0]), self.data1.open[0], self.data1.high[0], self.data1.low[0], self.data1.close[0])

#         print("open orders: ", len(self.broker.open_orders))
#         self.broker.check_open_order_status()
#         self.broker.cancel_open_orders()
#         print("round:", self.round)
#         self.round += 1
#         print("position:", self.position.size, self.position.price)
#         price = self.data0.close[0]
#         if self.round == 1:           
#             self.buy(price=price - self.add_float, data=self.data)
#  #       elif self.round == 2:
#             #self.sell(price=price + self.add_float, data=self.data)
#         elif self.round == 3:
#             self.sell(price=price + self.add_float, data=self.data)
#         elif self.round == 4:
#             self.buy(price=price - self.add_float, data=self.data)
            

    def notify_order(self, order):
        print(order)

if __name__ == '__main__':
    cerebro = bt.Cerebro(quicknotify=True)

    store = WindStore(logonAccount="M5Q1V8R2732",
                      password="0",
                      accountType="CFE",
                      target="T2212.CFE")
    broker = store.getbroker()
    cerebro.setbroker(broker)

    from_date = datetime.datetime.utcnow() - datetime.timedelta(minutes=600)
    #from_date = None

    
   

    cerebro.addstrategy(RSIStrategy)

    data = store.getdata(
        timeframe_in_minutes=bt.TimeFrame.Ticks,
        start_date=from_date)

    cerebro.adddata(data)

    cerebro.resampledata(data, timeframe=bt.TimeFrame.Seconds, compression=10)

    cerebro.run()
