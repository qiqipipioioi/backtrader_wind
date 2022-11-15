import datetime as dt

import backtrader as bt

from bt_wind.windstore import WindStore


class RSIStrategy(bt.Strategy):
    def __init__(self):
        #self.rsi = bt.indicators.RSI(period=2)  # RSI indicator
        #self.rma = bt.indicators.EMA(period=2)
        self.round = 0

    def next(self):
        print("open orders: ", len(self.broker.open_orders))
        self.broker.check_open_order_status()
        print("round:", self.round)
        self.round += 1
        print("position:", self.position.size, self.position.price)
        price = self.data0.close[0]
        if self.round == 1:           
            self.buy(price=price, data=self.data)
        elif self.round == 2:
            self.sell(price=price, data=self.data)
            

        # print('Open: {}, High: {}, Low: {}, Close: {}'.format(
        #     self.data.open[0],
        #     self.data.high[0],
        #     self.data.low[0],
        #     self.data.close[0]))
        # print('RSI: {}'.format(self.rma[0]))
        

        # if not self.position:
        #     print(self.rma[0])
        #     if self.rma[0] < 200:  # Enter long
        #         price = self.data0.close[0]
        #         print(price)
        #         self.buy(price = price)
        # else:
        #     print(self.rma[0])
        #     if self.rma[0] > 200:
        #         price = self.data0.close[0]
        #         self.sell(price = price)  # Close long position

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
