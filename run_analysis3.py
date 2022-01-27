import pandas as pd
import yfinance as yf
import datetime

from stock import Stock
from DCF_model import DiscountedCashFlowModel
from TA import SimpleMovingAverages
from TA import ExponentialMovingAverages
from TA import RSI

def run():
    ''' 
    Read in the input file. 
    Call the DCF to compute its DCF value and add the following columns to the output file.
    You are welcome to add additional valuation metrics as you see fit

    Symbol
    EPS Next 5Y in percent
    DCF Value
    Current Price
    Sector
    Market Cap
    Beta
    Total Assets
    Total Debt
    Free Cash Flow
    P/E Ratio
    Price to Sale Ratio
    RSI
    10 day EMA
    20 day SMA
    50 day SMA
    200 day SMA

    '''
    input_fname = "StockUniverse.csv"
    output_fname = "StockUniverseOutput.csv"

    
    as_of_date = datetime.date(2021, 12, 1)
    df = pd.read_csv(input_fname)
    out_df = pd.read_csv(output_fname)
    results = []
    for index, row in df.iterrows():
        
        stock = Stock(row['Symbol'], 'annual')
        model = DiscountedCashFlowModel(stock, as_of_date)
        
        stock.get_daily_hist_price('2020-01-1', '2021-12-1')

        periods = [9, 10, 20, 50, 100, 200]
        smas = SimpleMovingAverages(stock.ohlcv_df, periods)
        emas = ExponentialMovingAverages(stock.ohlcv_df, periods)
    
        emas.run()
        smas.run()
    
        e10 = emas.get_series(10)
        date = '2021-12-1'
        
        s200 = smas.get_series(200)
        s50 = smas.get_series(50)
        s20 = smas.get_series(20)        
        
        sbux = yf.Ticker(stock.symbol)
        
        balance = stock.yfinancial.get_financial_stmts('quarterly', 'balance')
        balance = balance.get('balanceSheetHistoryQuarterly').get(stock.symbol)[0]
        key = list(balance.keys())[0]
        total_assets = balance.get(key).get('totalAssets')
        
        relative_strength_index = RSI(stock.ohlcv_df, 14)       
        relative_strength_index.run()
        rsi = relative_strength_index.rsi.loc[date]
        
        short_term_growth_rate = float(row['EPS Next 5Y in percent'])/100
        medium_term_growth_rate = short_term_growth_rate/2
        long_term_growth_rate = 0.04
        
        model.set_FCC_growth_rate(short_term_growth_rate, medium_term_growth_rate, long_term_growth_rate)
        print(stock.symbol)
        fair_value = model.calc_fair_value()
        free_cashflow = stock.get_free_cashflow()
        beta = stock.get_beta()
        market_cap = stock.yfinancial.get_market_cap()
        p_e_ratio = stock.yfinancial.get_pe_ratio()
        p_s_ratio = stock.yfinancial.get_price_to_sales()
        total_debt = stock.get_total_debt()
        current_price = stock.yfinancial.get_current_price()
        sector = sbux.info['sector']
        print(f'The fair value is {fair_value}')
        print(f"Free Cash Flow for {stock.symbol} is {free_cashflow}")
        print(f'The beta is {beta}')
        print(f'The market cap is {market_cap}')
        print(f'The P/E ratio is {p_e_ratio}')
        print(f'The P/S ratio is {p_s_ratio}')
        print(f'The total debt is {total_debt}')
        print(f'The current price is {current_price}')
        print(f'The sector is {sector}')
        print(f'The 10 day EMA is {e10[date]}')
        print(f'The 200 day SMA is {s200[date]}')
        print(f'The 50 day SMA is {s50[date]}')
        print(f'The 20 day SMA is {s20[date]}')
        print(f'The total assets is {total_assets}')
        print(f'The RSI is {rsi}')
        
        results.append([row['Symbol'], 
                        row['EPS Next 5Y in percent'],
                        fair_value,
                        current_price,
                        sector,
                        market_cap,
                        beta,
                        total_assets,
                        total_debt,
                        free_cashflow,
                        p_e_ratio,
                        p_s_ratio,
                        rsi,
                        e10[date],
                        s20[date],
                        s50[date],
                        s200[date]])
        # pull additional fields
        # ...
    
    print('Done')
    output_df = pd.DataFrame(results, columns = ['Symbol', 
                                                 'EPS Next 5Y in percent',
                                                 'DCF value',
                                                 'Current Price',
                                                 'Sector',
                                                 'Market Cap',
                                                 'Beta',
                                                 'Total Assets',
                                                 'Total Debt',
                                                 'Free Cash Flow',
                                                 'P/E Ratio',
                                                 'P/S Ratio',
                                                 'RSI',
                                                 '10 Day EMA',
                                                 '20 day SMA',
                                                 '50 day SMA',
                                                 '200 day SMA'])
    print(output_df)
    output_df.to_csv(output_fname, index = False)
    # save the output into a StockUniverseOutput.csv file
    
    # ....

    
if __name__ == "__main__":
    run()
