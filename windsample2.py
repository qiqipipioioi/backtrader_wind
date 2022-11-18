import datetime
import time
from math import copysign

import backtrader as bt
from backtrader.utils import num2date
import backtrader.indicators as btind 

from bt_wind.windstore import WindStore

_ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(3)

class RSIStrategy(bt.Strategy):

    params = (('margin', 0.02),
              ('mult', 10000),
              ('close_lost', -100),
              ('fix_size', 2),
              ('flip', 0.005),
              ('wait_fill', 10)
    )

    def __init__(self):
        self.add_flip = 0.005
        self.count = 0
        self.ac = 0
        self.stop_lost = self.p.close_lost
        self.max_profit = 0
        #if self.data.open[0]


    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))



    def limit_line(self):
        high =  self.data1.high
        low = self.data1.low
        arr_high = []
        arr_low = []
        # 最近10根k线
        for i in range(-10,-1):
            arr_high.append(high[i])
            arr_low.append(low[i])

        bottom = min(arr_low)
        top = max(arr_high)

        return top,bottom


    # 买入信号
    def signal_buy(self):
        top , bottom = self.limit_line()
        # 开盘价突破上轨
        if self.data.close[0] > top:
            return True
        else:
            return False

    # 做空信号
    def signal_sell(self):
        top , bottom = self.limit_line()
        if self.data.close[0] < bottom:
            return True
        else:
            return False


    def next(self):


        if self.data._state != _ST_LIVE:
            return 

        if self.count > 0:
            self.count -= 1
            return


        #self.broker.sync_position()
        self.broker.check_open_order_status()
        self.broker.cancel_open_orders()

        price = self.data.open[0]


        print('ac:', self.ac)
        self.ac += 1
        print("data status,", self.data._state)
        print("open orders: ", len(self.broker.open_orders))
        print('position', self.position.size, self.position.price)
        print("data len", len(self.data))
        print("data1 len", len(self.data1))
        print("value,", self.broker.getvalue())
        print("limit line,", self.limit_line())
        print("now close,", price)
        if self.position.size != 0:
            now_profit = (self.data.close[0] - self.position.price) * self.p.mult * self.position.size/ abs(self.position.size) 
            print('now_profit', now_profit)

        if self.position.size > 0 :
            # 更新最高价用于上调止损点
            self.now_profit = (self.data.close[0] - self.position.price) * self.p.mult * self.position.size/ abs(self.position.size) 
            #print(self.data.open[0], self.buy_price, self.now_profit, self.stop_lost)

            # 利润跌破止损线则平仓
            if self.now_profit < self.stop_lost:
                # 执行卖出
                #print('1')
                self.order = self.sell(data=self.data, size = abs(self.position.size), price = price - self.p.flip)
                self.count = self.p.wait_fill
            if self.now_profit > self.max_profit:
                self.max_profit = self.now_profit
                self.stop_lost = self.max_profit + self.p.close_lost
            return
        elif self.position.size < 0 :
            # 更新最高价用于上调止损点
            self.now_profit = (self.data.close[0] - self.position.price) * self.p.mult * self.position.size/ abs(self.position.size) 
            #print(self.data.open[0], self.buy_price, self.now_profit, self.stop_lost)

            # 利润跌破止损线则平仓
            if self.now_profit < self.stop_lost:
                # 执行卖出
                #print('1')
                self.order = self.buy(data=self.data, size = abs(self.position.size), price = price + self.p.flip)
                self.count = self.p.wait_fill
            if self.now_profit > self.max_profit:
                self.max_profit = self.now_profit
                self.stop_lost = self.max_profit + self.p.close_lost
            return
            

        else :  # 没有持仓
            if self.signal_buy():
                # 执行买入
                self.order = self.buy(data=self.data, size = self.p.fix_size, price = price + self.p.flip )
                self.count = self.p.wait_fill
                self.max_profit = 0
                self.stop_lost = self.p.close_lost
                #print('3')

            elif self.signal_sell():
                # 执行买入
                self.order = self.sell(data=self.data, size = self.p.fix_size, price = price - self.p.flip )
                self.count = self.p.wait_fill
                self.max_profit = 0
                self.stop_lost = self.p.close_lost
                #print('4')
            return
          


    def notify_order(self, order):
        # 未被处理的订单
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 已被处理的订单
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, ref:%.4f, Price: %.4f, Size: %.2f, Cost: %.4f, Comm %.4f' %
                    (order.ref,
                     order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm))
            else:  # Sell
                self.log('SELL EXECUTED, ref:%.4f, Price: %.4f, Size: %.2f, Cost: %.4f, Comm %.4f' %
                        (order.ref,
                        order.executed.price,
                         order.executed.size,
                        order.executed.value,
                        order.executed.comm))
                
    def notify_trade(self, trade):
        # 交易刚打开时
        if trade.justopened: 
            self.log('Trade Opened, name: %s, Size: %.2f,Price: %.2f' % (
                    trade.getdataname(), trade.size, trade.price))
        # 交易结束   
        elif trade.isclosed:
            self.log('Trade Closed, name: %s, GROSS %.2f, NET %.2f, Comm %.2f' %(
            trade.getdataname(), trade.pnl, trade.pnlcomm, trade.commission))
        # 更新交易状态
        else: 
            self.log('Trade Updated, name: %s, Size: %.2f,Price: %.2f' % (
                    trade.getdataname(), trade.size, trade.price))   


                 

        

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
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Seconds, compression=2)

    cerebro.run()
