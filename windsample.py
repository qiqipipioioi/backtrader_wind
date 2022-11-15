import datetime as dt

import backtrader as bt

from bt_wind.windstore import WindStore


class RSIStrategy(bt.Strategy):
    def __init__(self):
        #self.rsi = bt.indicators.RSI(period=2)  # RSI indicator
        #self.rma = bt.indicators.EMA(period=2)
        self.round = 0
        self.add_float = 0.01

    def next(self):
        print("open orders: ", len(self.broker.open_orders))
        self.broker.check_open_order_status()
        self.broker.cancel_open_orders()
        print("round:", self.round)
        self.round += 1
        print("position:", self.position.size, self.position.price)
        price = self.data0.close[0]
        if self.round == 1:           
            self.buy(price=price - self.add_float, data=self.data)
 #       elif self.round == 2:
            #self.sell(price=price + self.add_float, data=self.data)
        elif self.round == 3:
            self.sell(price=price + self.add_float, data=self.data)
        elif self.round == 4:
            self.buy(price=price - self.add_float, data=self.data)
            

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

    #from_date = dt.datetime.utcnow() - dt.timedelta(minutes=600)
    from_date = None
    data = store.getdata(
        timeframe_in_minutes=5,
        start_date=from_date)

    cerebro.addstrategy(RSIStrategy)
    cerebro.adddata(data)
    cerebro.run()
