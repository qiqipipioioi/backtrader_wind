from collections import deque

import pandas as pd
import time

from backtrader.dataseries import TimeFrame
from backtrader.feed import DataBase
from backtrader.utils import date2num
import datetime
from WindPy import *


class WindData(DataBase):
    params = (
        ('drop_newest', True),
    )
    
    # States for the Finite State Machine in _load
    _ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(3)

    RTBAR_MINSIZE = (TimeFrame.Ticks, 1)


    def __init__(self, store, timeframe_in_minutes, start_date=None):
        self.RTBAR_MINSIZE = (timeframe_in_minutes, 1)
        self.start_date = start_date

        self._store = store
        self._data = deque()
        self._state = None

        self.symbol_info = self._store.get_symbol_info(self._store.symbol)

    
    def datacallback(self, indata: w.WindData):
        if indata.ErrorCode!=0:
            print('error code:'+str(indata.ErrorCode)+'\n')
            return()
        
        this_datetime = indata.Times[0]
        this_open = indata.Data[-2][0]
        this_high = indata.Data[-2][0]
        this_low = indata.Data[-2][0]
        this_last = indata.Data[-2][0]
        this_vol = indata.Data[-1][0]
        this_data = [this_datetime, this_open, this_high, this_low, this_last, this_vol]

        self._data.append(this_data)
        


    def _load(self):
        if self._state == self._ST_OVER:
            return False
        elif self._state == self._ST_LIVE:
            return self._load_data()
        elif self._state == self._ST_HISTORBACK:
             if self._load_data():
                 return True
             else:
                self._start_live()
    
    def _load_data(self):
        try:
            data = self._data.popleft()
        except IndexError:
            return None
        print("add real time data", datetime.now())
        self.lines.datetime[0] = date2num(data[0])
        self.lines.open[0] = data[1]
        self.lines.high[0] = data[2]
        self.lines.low[0] = data[3]
        self.lines.close[0] = data[4]
        self.lines.volume[0] = data[5]
        self.lines.openinterest[0] = -1
        return True


    def _start_live(self):
        self._state = self._ST_LIVE
        self.put_notification(self.LIVE)
        self._store.subscribe_realtime_data(self.symbol_info, self.datacallback)

    def haslivedata(self):
        return self._state == self._ST_LIVE and self._data

    def islive(self):
        return True
        
    def start(self):
        DataBase.start(self)
        
        if self.symbol_info is None:
            self._state = self._ST_OVER
            self.put_notification(self.NOTSUBSCRIBED)
            return

        if self.start_date:
            self._state = self._ST_HISTORBACK
            self.put_notification(self.DELAYED)
            start_date_str = datetime.strftime(self.start_date, "%Y-%m-%d %H:%M:%S")
            result = self._store.get_history_data(self.symbol_info, start_date_str)
            thedata = list(zip(result.Times, result.Data[0], result.Data[1], result.Data[2], result.Data[3], result.Data[4]))
        
            self._data.extend(thedata)            
        else:
            self._start_live()
