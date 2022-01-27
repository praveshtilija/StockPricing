import math
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from bisection_method import bisection

import enum
import calendar

from datetime import date

from bond import Bond, DayCount, PaymentFrequency


def get_actual360_daycount_frac(start, end):
    day_in_year = 360
    day_count = (end - start).days
    return(day_count / day_in_year)

def get_30360_daycount_frac(start, end):
    day_in_year = 360
    day_count = 360*(end.year - start.year) + 30*(end.month - start.month - 1) + \
                max(0, 30 - start.day) + min(30, end.day)
    return(day_count / day_in_year )
    

def get_actualactual_daycount_frac(start, end):
    end_of_year = date(start.year, 12, 31)
    beginning_of_year = date(start.year, 1, 1)
    days_in_the_year = (end_of_year - beginning_of_year).days + 1

    num_days_btwn_strt_n_end = (end-start).days
    result = num_days_btwn_strt_n_end / days_in_the_year
    return(result)

class BondCalculator(object):
    '''
    Bond Calculator class for pricing a bond
    '''

    def __init__(self, pricing_date):
        self.pricing_date = pricing_date

    def calc_one_period_discount_factor(self, bond, yld):
        # calculate the future cashflow vectors
        df = None
        if bond.payment_freq == PaymentFrequency.ANNUAL:
            df = 1/(1+yld)
        elif bond.payment_freq == PaymentFrequency.SEMIANNUAL:
            df = 1/(1+(yld/2))
        elif bond.payment_freq == PaymentFrequency.QUARTERLY:
            df = 1/(1+(yld/4))
        elif bond.payment_freq == PaymentFrequency.MONTHLY:
            df = 1/(1+(yld/12))
        else:
            raise Exception("Unsupported Payment frequency")
        
        return(df)


    def calc_clean_price(self, bond, yld):
        '''
        Calculate bond price as of the pricing_date for a given yield
        bond price should be expressed in percentage eg 100 for a par bond
        '''
        result = None       
        one_period_factor = self.calc_one_period_discount_factor(bond, yld)
        discount_factor = [math.pow(one_period_factor, i+1) for i in range(len(bond.coupon_payment))]
        cash_flow = [i for i in bond.coupon_payment]
        cash_flow[len(cash_flow) - 1] += bond.principal
        present_values = [cash_flow[i] * discount_factor[i] for i in range(len(bond.coupon_payment))]
        result = sum(present_values)
        
        
        return(result)

    def calc_accrual_interest(self, bond, settle_date):
        '''
        calculate the accrual interest on given a settle_date
        by calculating the previous payment date first and use the date count
        from previous payment date to the settle_date
        '''
        prev_pay_date = bond.get_previous_payment_date(settle_date)
        end_date = settle_date

        if (bond.day_count == DayCount.DAYCOUNT_30360):
            frac = get_30360_daycount_frac(prev_pay_date, settle_date)
        elif (bond.day_count == DayCount.DAYCOUNT_ACTUAL_360):
            frac = get_actual360_daycount_frac(prev_pay_date, settle_date)
        elif (bond.day_count == DayCount.DAYCOUNT_ACTUAL_ACTUAL):
            frac = get_actualactual_daycount_frac(prev_pay_date, settle_date)

        result = frac * bond.coupon * bond.principal/100

        return(result)

    def calc_macaulay_duration(self, bond, yld):
        '''
        time to cashflow weighted by PV
        '''
        one_period_factor = self.calc_one_period_discount_factor(bond, yld)
        discount_factor = [math.pow(one_period_factor, i+1) for i in range(len(bond.coupon_payment))]
        cash_flow = [i for i in bond.coupon_payment]
        cash_flow[len(cash_flow) - 1] += bond.principal
        PVs = [cash_flow[i] * discount_factor[i] for i in range(len(bond.coupon_payment))]
        wavg = [bond.payment_times_in_year[i] * PVs[i] for i in range(len(bond.coupon_payment))]
        result =(sum(wavg) / sum(PVs))

        return(result)

    def calc_modified_duration(self, bond, yld):
        '''
        calculate modified duration at a certain yield yld
        '''
        D = self.calc_macaulay_duration(bond, yld)
        result = None
        if bond.payment_freq == PaymentFrequency.ANNUAL:
            result = D/(1 + yld)
        elif bond.payment_freq == PaymentFrequency.SEMIANNUAL:
            result = D/(1 + (yld/2))
        elif bond.payment_freq == PaymentFrequency.QUARTERLY:
            result = D/(1 + (yld/4))
        elif bond.payment_freq == PaymentFrequency.MONTHLY:
            result = D/(1 + (yld/12))
        else:
            raise Exception("Unsupported Payment frequency")
            
        return(result)

    def calc_yield(self, bond, bond_price):
        '''
        Calculate the yield to maturity on given a bond price using bisection method
        '''

        def match_price(yld):
            calculator = BondCalculator(self.pricing_date)
            px = calculator.calc_clean_price(bond, yld)
            return(px - bond_price)

        yld, n_iteractions = bisection(match_price, 0, 1000, eps = 10e-6)
        return(yld)
    
    def calc_convexity(self, bond, yld):    
        one_period_factor = self.calc_one_period_discount_factor(bond, yld)
        print(one_period_factor)
        discount_factor = [(one_period_factor ** (i+1)) for i in range(len(bond.coupon_payment))]
        print(discount_factor)
        cash_flow = [i for i in bond.coupon_payment]
        cash_flow[len(cash_flow) - 1] += bond.principal
        print(cash_flow)
        PVs = [ cash_flow[i] * discount_factor[i] for i in range(len(bond.coupon_payment))]
        print(PVs)
        weight = [PVs[i]/sum(PVs) for i in range(len(bond.coupon_payment))]
        print(weight)
        print(bond.payment_times_in_year)
        result = [(bond.payment_times_in_year[i] ** 2) * weight[i] for i in range(len(bond.coupon_payment))]
        print(result)
        return(sum(result))


##########################  some test cases ###################

def _example2():
    pricing_date = date(2021, 1, 1)
    issue_date = date(2021, 1, 1)
    engine = BondCalculator(pricing_date)

    # Example 2
    #bond = Bond(issue_date, term=10, day_count = DayCount.DAYCOUNT_30360,
                 #payment_freq = PaymentFrequency.ANNUAL, coupon = 0.05)

    #yld = 0.06
    #px_bond2 = engine.calc_clean_price(bond, yld)
    #print("The clean price of bond 2 is: ", format(px_bond2, '.4f'))
    price = 103.72
    bond = Bond(issue_date, term=6, day_count=DayCount.DAYCOUNT_30360,
                payment_freq=PaymentFrequency.SEMIANNUAL, coupon=0.08, principal=1000)

    yld = 0.1
    px_bond9 = engine.calc_convexity(bond, yld)
    print("The price of bond 9 is: ", format(px_bond9, '.4f'))
    #assert( abs(px_bond2 - 92.640) < 0.01)

    
def _example3():
    pricing_date = date(2021, 1, 1)
    issue_date = date(2021, 1, 1)
    engine = BondCalculator(pricing_date)

    
    bond = Bond(issue_date, term = 2, day_count =DayCount.DAYCOUNT_30360,
                 payment_freq = PaymentFrequency.SEMIANNUAL,
                 coupon = 0.08)

    yld = 0.06
    px_bond3 = engine.calc_clean_price(bond, yld)
    print("The clean price of bond 3 is: ", format(px_bond3, '.4f'))
    assert( abs(px_bond3 - 103.717) < 0.01)


def _example4():
    # unit tests
    pricing_date = date(2021, 1, 1)
    issue_date = date(2021, 1, 1)
    engine = BondCalculator(pricing_date)

    # Example 4 5Y bond with semi-annual 5% coupon priced at 103.72 should have a yield of 4.168%
    price = 103.72
    bond = Bond(issue_date, term=5, day_count = DayCount.DAYCOUNT_30360,
                payment_freq = PaymentFrequency.SEMIANNUAL, coupon = 0.05, principal = 100)
    

    yld = engine.calc_yield(bond, price)

    print("The yield of bond 4 is: ", yld*100)
    px_bond2 = engine.calc_convexity(bond, yld)
    print("The convexity of bond 4 is: ", format(px_bond2, '.4f'))
    assert( abs(yld - 0.04168) < 0.01)

def _example5():
    # unit tests
    pricing_date = date(2021, 1, 1)
    issue_date = date(2021, 1, 1)
    engine = BondCalculator(pricing_date)

    # Example 4 5Y bond with semi-annual 5% coupon priced at 103.72 should have a yield of 4.168%
    price = 103.72
    bond = Bond(issue_date, term=5, day_count=DayCount.DAYCOUNT_30360,
                payment_freq=PaymentFrequency.SEMIANNUAL, coupon=0.05, principal=100)

    yld = engine.calc_yield(bond, price)

    print("The yield of bond 4 is: ", yld)

    assert (abs(yld - 0.04168) < 0.01)

def _test():
    # basic test cases
    #_example2()
    #_example3()
    #_example4()
    _example5()

    

if __name__ == "__main__":
    _test()
