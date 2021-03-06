import enum
import calendar
import math
import pandas as pd
import numpy as np

import datetime 
from scipy.stats import norm

from math import log, exp, sqrt

from stock import Stock

class DiscountedCashFlowModel(object):
    '''
    DCF Model:

    FCC is assumed to go have growth rate by 3 periods, each of which has different growth rate
           short_term_growth_rate for the next 5Y
           medium_term_growth_rate from 6Y to 10Y
           long_term_growth_rate from 11Y to 20thY
    '''

    def __init__(self, stock, as_of_date):
        self.stock = stock
        self.as_of_date = as_of_date

        self.short_term_growth_rate = None
        self.medium_term_growth_rate = None
        self.long_term_growth_rate = None


    def set_FCC_growth_rate(self, short_term_rate, medium_term_rate, long_term_rate):
        self.short_term_growth_rate = short_term_rate
        self.medium_term_growth_rate = medium_term_rate
        self.long_term_growth_rate = long_term_rate


    def calc_fair_value(self):
        '''
        calculate the fair_value using DCF model as follows

        1. calculate a yearly discount factor using the WACC
        2. Get the Free Cash flow
        3. Sum the discounted value of the FCC for the 20 years using similar approach as presented in class
        4. Compute the PV as cash + short term investments - total debt + the above sum of discounted free cash flow
        5. Return the stock fair value of the stock
        '''
        results = None
        FreeCashFlow = self.stock.get_free_cashflow()
        CurrentCash = self.stock.get_cash_and_cash_equivalent()
        WACC = self.stock.lookup_wacc_by_beta(self.stock.get_beta())
        TotalDebt = self.stock.get_total_debt()
        Shares = self.stock.get_num_shares_outstanding()
        DiscountFactor = 1 / (1 + WACC)
        EPS5Y = self.short_term_growth_rate
        EPS6To10Y = self.medium_term_growth_rate
        EPS10To20Y = self.long_term_growth_rate
        DCF = 0
        for i in range(1, 6):
            DCF += FreeCashFlow * (1 + EPS5Y) ** i * DiscountFactor ** i

        CF5 = FreeCashFlow * (1 + EPS5Y) ** 5
        for i in range(1, 6):
            DCF += CF5 * (1 + EPS6To10Y) ** i * DiscountFactor ** (i + 5)

        CF10 = CF5 * (1 + EPS6To10Y) ** 5
        for i in range(1, 11):
            DCF += CF10 * (1 + EPS10To20Y) ** i * DiscountFactor ** (i + 10)

        PresentValue = CurrentCash - TotalDebt + DCF
        results = PresentValue / Shares
        return(results)


def _test():
    symbol = 'AAPL'
    as_of_date = datetime.date(2021, 11, 1)

    stock = Stock(symbol)
    model = DiscountedCashFlowModel(stock, as_of_date)

    print("Shares ", stock.get_num_shares_outstanding())
    print("FCC ", stock.get_free_cashflow())
    beta = stock.get_beta()
    wacc = stock.lookup_wacc_by_beta(beta)
    print("Beta ", beta)
    print("WACC ", wacc)
    print("Total debt ", stock.get_total_debt())
    print("cash ", stock.get_cash_and_cash_equivalent())

    # look up EPS next 5Y from Finviz
    eps5y = 0.1543
    model.set_FCC_growth_rate(eps5y, eps5y/2, 0.04)

    model_price = model.calc_fair_value()
    print(f"DCF price for {symbol} as of {as_of_date} is {model_price}")
    

if __name__ == "__main__":
    _test()
