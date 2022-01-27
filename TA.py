import enum
import calendar
import math
import pandas as pd
import numpy as np

from datetime import date
from scipy.stats import norm
from dateutil.relativedelta import relativedelta

from math import log, exp, sqrt

from stock import *

class SimpleMovingAverages(object):
    '''
    On given a OHLCV data frame, calculate corresponding simple moving averages
    '''
    def __init__(self, ohlcv_df, periods):
        #
        self.ohlcv_df = ohlcv_df
        self.periods = periods
        self._sma = {}

    def _calc(self, period, price_source):
        '''
        for a given period, calc the SMA as a pandas series from the price_source
        which can be  open, high, low or close
        '''
        result = self.ohlcv_df[price_source].rolling(period, min_periods = 1).mean()
        return(result)
        
    def run(self, price_source = 'Close'):
        '''
        Calculate all the simple moving averages as a dict
        '''
        for period in self.periods:
            self._sma[period] = self._calc(period, price_source)
    
    def get_series(self, period):
        return(self._sma[period])

    
class ExponentialMovingAverages(object):
    '''
    On given a OHLCV data frame, calculate corresponding simple moving averages
    '''
    def __init__(self, ohlcv_df, periods):
        #
        self.ohlcv_df = ohlcv_df
        self.periods = periods
        self._ema = {}

    def _calc(self, period):
        '''
        for a given period, calc the SMA as a pandas series
        '''
        result = self.ohlcv_df['Close'].ewm(span = period).mean()
        return(result)
        
    def run(self):
        '''
        Calculate all the simple moving averages as a dict
        '''
        for period in self.periods:
            self._ema[period] = self._calc(period)

    def get_series(self, period):
        return(self._ema[period])


class RSI(object):

    def __init__(self, ohlcv_df, period = 14):
        self.ohlcv_df = ohlcv_df
        self.period = period
        self.rsi = None

    def get_series(self):
        return(self.rsi)

    def run(self):
        '''
        calculate RSI
        '''
        diff = self.ohlcv_df['Adj Close'].diff(1).dropna()  # diff in one field(one day)

        # this preservers dimensions off diff values
        up_chg = 0 * diff
        down_chg = 0 * diff

        # up change is equal to the positive difference, otherwise equal to zero
        up_chg[diff > 0] = diff[diff > 0]

        # down change is equal to negative deifference, otherwise equal to zero
        down_chg[diff < 0] = diff[diff < 0]

        # check pandas documentation for ewm
        # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.ewm.html
        # values are related to exponential decay
        # we set com=time_window-1 so we get decay alpha=1/time_window
        up_chg_avg = up_chg.ewm(com=self.period - 1, min_periods=self.period).mean()
        down_chg_avg = down_chg.ewm(com=self.period - 1, min_periods=self.period).mean()

        rs = abs(up_chg_avg / down_chg_avg)
        self.rsi = 100 - 100 / (1 + rs)
        return (self.rsi)

class VWAP(object):

    def __init__(self, ohlcv_df):
        self.ohlcv_df = ohlcv_df
        self.vwap = None

    def get_series(self):
        return(self.vwap)

    def run(self):
        '''
        calculate VWAP
        '''
        Price = (self.ohlcv_df['High'] + self.ohlcv_df['Low'] + self.ohlcv_df['Close']) / 3
        self.vwap = ((self.ohlcv_df['Volume'] * Price).cumsum()) / self.ohlcv_df['Volume'].cumsum()
        return(self.vwap)


def _test():
    # simple test cases
    symbol = 'AAPL'
    stock = Stock(symbol)
    start_date = datetime.date(2020, 1, 1)
    end_date = datetime.date.today()

    stock.get_daily_hist_price('2019-11-1', '2021-11-1')
    
    vwap = VWAP(stock.ohlcv_df)
    v1 = vwap.run()
    print(v1)

    #periods = [9, 20, 50, 100, 200]
    #smas = SimpleMovingAverages(stock.ohlcv_df, periods)
    #smas.run()
    #s1 = smas.get_series(9)
    #print(s1.index)
    #print(s1)

    #stock.get_daily_hist_price('2020-01-1', '2021-12-1')

    #periods = [9, 10, 20, 50, 100, 200]
    #smas = SimpleMovingAverages(stock.ohlcv_df, periods)
    #emas = ExponentialMovingAverages(stock.ohlcv_df, periods)
    
    #emas.run()
    #smas.run()
    
    #e1 = emas.get_series(10)
    #date = '2021-12-1'
    #print(f'10 day EMA: {e1[date]}')
    
    #s1 = smas.get_series(200)
    #s2 = smas.get_series(50)
    #s3 = smas.get_series(20)
    #print(s1.index)
    #print(f'200 day SMA: {s1[date]}')
    #print(f'50 day SMA: {s2[date]}')
    #print(f'20 day SMA: {s3[date]}')

    #rsi_indicator = RSI(stock.ohlcv_df)
    #rsi_indicator.run()

    #print(f"RSI for {symbol} is {rsi_indicator.rsi}")
    #print(rsi_indicator.rsi.loc['2021-12-1'])
    

if __name__ == "__main__":
    _test()

