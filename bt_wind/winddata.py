from collections import deque

import pandas as pd
import time

from backtrader.dataseries import TimeFrame
from backtrader.feed import DataBase
from backtrader.utils import date2num
import datetime


class WindData(DataBase):
    params = (
        ('drop_newest', True),
    )
    
    # States for the Finite State Machine in _load
    #_ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(3)
    _ST_OVER = 0
    _ST_LIVE = 1

    def __init__(self, store, timeframe_in_minutes, start_date=None):
        self.timeframe_in_minutes = timeframe_in_minutes
        self.start_date = start_date

        self._store = store
        self._data = deque()
        self._state = None

        self.symbol_info = self._store.get_symbol_info(self._store.symbol)

    # def _handle_kline_socket_message(self, msg):
    #     """https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-streams"""
    #     if msg['e'] == 'kline':
    #         if msg['k']['x']:  # Is closed
    #             kline = self._parser_to_kline(msg['k']['t'], msg['k'])
    #             self._data.extend(kline.values.tolist())
    #     elif msg['e'] == 'error':
    #         raise msg

    def _load(self):
        if self._state == self._ST_OVER:
            return False
        # elif self._state == self._ST_LIVE:
        #     return self._load_kline()
        # elif self._state == self._ST_HISTORBACK:
        #     if self._load_kline():
        #         return True
        else:
            self._start_live()
            return True

    # def _load_kline(self):
    #     try:
    #         kline = self._data.popleft()
    #     except IndexError:
    #         return None

    #     timestamp, open_, high, low, close, volume = kline

    #     self.lines.datetime[0] = date2num(timestamp)
    #     self.lines.open[0] = open_
    #     self.lines.high[0] = high
    #     self.lines.low[0] = low
    #     self.lines.close[0] = close
    #     self.lines.volume[0] = volume
    #     return True
    
    # def _parser_dataframe(self, data):
    #     df = data.copy()
    #     df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    #     df['timestamp'] = df['timestamp'].values.astype(dtype='datetime64[ms]')
    #     df['open'] = df['open'].values.astype(float)
    #     df['high'] = df['high'].values.astype(float)
    #     df['low'] = df['low'].values.astype(float)
    #     df['close'] = df['close'].values.astype(float)
    #     df['volume'] = df['volume'].values.astype(float)
    #     # df.set_index('timestamp', inplace=True)
    #     return df
    
    # def _parser_to_kline(self, timestamp, kline):
    #     df = pd.DataFrame([[timestamp, kline['o'], kline['h'],
    #                         kline['l'], kline['c'], kline['v']]])
    #     return self._parser_dataframe(df)
    
    def _start_live(self):
        self._state = self._ST_LIVE
        self.put_notification(self.LIVE)
        time.sleep(5)
        print("add real time data", datetime.datetime.now())
        result = self._store.get_realtime_data(self.symbol_info)
        
        self.lines.datetime[0] = date2num(result.Times[0])
        self.lines.open[0] = result.Data[0][0]
        self.lines.high[0] = result.Data[1][0]
        self.lines.low[0] = result.Data[2][0]
        self.lines.close[0] = result.Data[3][0]
        self.lines.volume[0] = result.Data[4][0]
        self.lines.openinterest[0] = -1



        # self._store.binance_socket.start_kline_socket(
        #     self._handle_kline_socket_message,
        #     self.symbol_info['symbol'],
        #     self.interval)
        
    def haslivedata(self):
        return self._state == self._ST_LIVE and self._data

    def islive(self):
        return True
        
    def start(self):
        DataBase.start(self)

        # self.interval = self._store.get_interval(TimeFrame.Minutes, self.timeframe_in_minutes)
        # if self.interval is None:
        #     self._state = self._ST_OVER
        #     self.put_notification(self.NOTSUPPORTED_TF)
        #     return
        
        
        if self.symbol_info is None:
            self._state = self._ST_OVER
            self.put_notification(self.NOTSUBSCRIBED)
            return

        if self.start_date:
            #self._state = self._ST_HISTORBACK
            self.put_notification(self.DELAYED)
            start_date_str = datetime.datetime.strftime(self.start_date, "%Y-%m-%d %H:%M:%S")
            result = self._store.get_history_data(self.symbol_info, start_date_str)
            thedata = list(zip(result.Times, result.Data[0], result.Data[1], result.Data[2], result.Data[3], result.Data[4]))
        
            self._data.extend(thedata)            
        else:
            self._start_live()
