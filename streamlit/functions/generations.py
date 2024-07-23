import yfinance as yf
import pandas_ta as ta
import pandas as pd
import streamlit as st

import math

class Generate_DB:
    def __init__(_self):
        #TODO add this documentation to get_database method.
        """
        Generates database with all of its metrics by providing it parameters.

        Arguments
        ----------
        ticker (str): Provide a ticker symbol.
            SP500 = ^GSPC\n
            S&P Energy = XLE\n
            S&P Utility = XLU\n
            S&P Consumer = XLY\n
            RSP = RSP\n
            Nasdaq = ^IXIC\n
            Russel 2000 = ^RUT\n
            VIX = ^VIX\n
            High Yield Corp Bond = HYG\n
        """
        _self.db = None
        _self.curr_rsi = None
        _self.curr_ma = None
        _self.curr_p = None
        _self.pctchg_int = None
        _self.pctchg_str = None
        _self.pctchg_floor_int = None
        _self.pctchg_ceil_int = None
    
    def get_database(_self, ticker: str, start_date: str, end_date: str, interval: str ="1d", rsi_value: int =22, ma_length: int = 50): #TODO modify so that MA and RSI don't automatically generate.
        _self.db = yf.download([ticker], start=start_date, end=end_date, interval=interval)
        
        # Database Massage
        _self.db['% Change'] = _self.db['Close'].pct_change()

        # (-) Columns
        _self.db = _self.db.drop(['Adj Close'], axis=1)

        _self.db['rsi'] = ta.rsi(close = _self.db.Close, length=rsi_value)
        _self.db['ma'] = ta.sma(close = _self.db.Close, length=ma_length)
        
        # (+) % Change
        _self.pctchg_int = _self.db["% Change"].iloc[-1] # % Change COLUMN
        _self.pctchg_str = "{:.2%}".format(_self.db["% Change"].iloc[-1]) # %Change current value
        # ---% Change FLOOR & CEILING
        _self.pctchg_floor_int = math.floor(_self.pctchg_int*100)/100
        _self.pctchg_ceil_int = math.ceil(_self.pctchg_int*100)/100
        
        # (+) RSI
        _self.curr_rsi = _self.db['rsi'].iloc[-1]
        # _self.curr_rsi = int(_self.db['rsi'].iloc[-1])

        # (+) Moving Average
        _self.curr_ma = (_self.db['ma'].iloc[-1])

        # get Current Price
        _self.curr_p = int(_self.db["Close"].iloc[-1])

    def generate_ratio(_self, numerator, denominator, start_date, end_date, interval, rsi_length:int=22, ma_length:int=50):
        '''
        Args:
        numerator or denominator: Nasdaq, S&P 500, Russel 2000, S&P 500 Equal Weight
        '''
        ticker_dict = {
            "Nasdaq": "^IXIC",
            "S&P 500": "^GSPC",
            "Russel 2000": "^RUT",
            "S&P 500 Equal Weight": "RSP"
        }

        numerator_cls = Generate_DB()
        numerator_ticker=ticker_dict.get(numerator)
        numerator_cls.get_database(ticker=numerator_ticker, start_date=start_date, end_date=end_date, interval=interval)
        numerator_cls.db.drop(['Open', 'High', 'Low', 'Volume', '% Change', 'ma', 'rsi'], axis = 1, inplace=True)
        numerator_cls.db.rename(columns={'Close': f'{numerator} Close'}, inplace=True)

        denominator_cls = Generate_DB()
        denominator_ticker=ticker_dict.get(denominator)
        denominator_cls.get_database(ticker=denominator_ticker, start_date=start_date, end_date=end_date, interval=interval)
        denominator_cls.db.drop(['Open', 'High', 'Low', 'Volume', '% Change', 'ma', 'rsi'], axis = 1, inplace=True)
        denominator_cls.db.rename(columns={'Close': f'{denominator} Close'},inplace=True)

        #Create Ratio Columns
        _self.db = pd.concat([numerator_cls.db, denominator_cls.db], axis=1)
        _self.db['Close']=_self.db[f'{numerator} Close']/_self.db[f'{denominator} Close']
        _self.db['% Change']=(_self.db['Close'].pct_change()*100).round(2)
        
        #Create rsi and ma columns
        _self.db['rsi'] = ta.rsi(close = _self.db['Close'], length=rsi_length)
        _self.db['ma'] = ta.sma(close = _self.db['Close'], length=ma_length)

        #Creating variables for UI
        _self.curr_rsi = _self.db['rsi'].iloc[-1]
        _self.curr_ma = int(_self.db['ma'].iloc[-1])
        _self.curr_p = _self.db['Close'].iloc[-1]
        _self.pctchg_int = _self.db['% Change'].iloc[-1]
        _self.pctchg_str = "{:.2%}".format(_self.pctchg_int / 100)

    def metric_vs_selection(_self, comparison_type:str, comparator:str, selected_value, sp500:pd.DataFrame, ndx:pd.DataFrame, rus2k:pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        '''
        Compares the current level price with the selected value.

        Args:
        comparison_type: current price, % change, price vs ma, rsi vs selection, ratio vs selection, ratio % change vs selection
        comparator: 'Greater than', 'Less than'

        Output:
        _self, sp500_intersection, ndx_intersection, rus2k_intersection
        '''
        ref_dict = {
            "current price": {
                "1st value": _self.curr_p,
                "2nd value": selected_value,
                "1st col": _self.db.get("Close", 0),
                "2nd col": selected_value
            },
            "% change": {
                "1st value": _self.pctchg_int*100,
                "2nd value": selected_value,
                "1st col": _self.db.get("% Change", 0)*100,
                "2nd col": selected_value
            },
            "price vs ma": {
                "1st value": _self.curr_p,
                "2nd value": _self.curr_ma,
                "1st col": _self.db.get("Close", 0),
                "2nd col": _self.db['ma']
            },
            "rsi vs selection": {
                "1st value": _self.curr_rsi,
                "2nd value": selected_value,
                "1st col": _self.db.get("rsi", 0),
                "2nd col": selected_value
            },
            "ratio vs selection": {
                "1st value": _self.curr_p,
                "2nd value": selected_value,
                "1st col": _self.db.get("Ratio", 0),
                "2nd col": selected_value
            },
            "ratio % change vs selection": {
                "1st value": _self.pctchg_int,
                "2nd value": selected_value,
                "1st col": _self.db.get("Ratio % Chg", 0),
                "2nd col": selected_value
            }
        }

        if comparator == 'Greater than':
            _self.boolean_comp = ref_dict[comparison_type]['1st value'] > ref_dict[comparison_type]['2nd value']

            filtered_database = _self.db[ref_dict[comparison_type]['1st col'] > ref_dict[comparison_type]['2nd col']]

        elif comparator == 'Less than':
            _self.boolean_comp = ref_dict[comparison_type]['1st value'] < ref_dict[comparison_type]['2nd value']

            filtered_database = _self.db[ref_dict[comparison_type]['1st col'] < ref_dict[comparison_type]['2nd col']]

        else:
            return "Check comparator value, should be either p greater or lower"

        sp500.append(filtered_database)
        ndx.append(filtered_database)
        rus2k.append(filtered_database)        

        return sp500, ndx, rus2k
    
    def metric_vs_comparison_cross(_self, comparison_type:str, selected_value:tuple, sp500:pd.DataFrame, ndx:pd.DataFrame, rus2k:pd.DataFrame, comparator:str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        '''
        Compares the current level price with the selected value.

        Args:
        comparison_type: current price, % change, % change between, price vs ma, rsi vs selection, ratio vs selection, ratio % change vs selection
        comparator: 'Greater than', 'Less than', 'Between'

        Output:
        _self, sp500_intersection, ndx_intersection, rus2k_intersection
        '''
        if len(selected_value) ==2:
            second_value = selected_value[0]
            third_value = float(selected_value[1])
        elif len(selected_value) == 1:
            second_value = selected_value[0]
            third_value = None
        elif len(selected_value) == 0:
            second_value = None
            third_value = None

        else: third_value = None
        ref_dict = {
            "current price": {
                "1st value": _self.curr_p,
                "2nd value": second_value,
                "1st col": "Close",
                "1st col x": 1,
                "2nd col": second_value,
                "3rd col": 0
            },
            "% change": {
                "1st value": _self.pctchg_int*100,
                "2nd value": second_value,
                "1st col": "% Change",
                "1st col x": 100,
                "2nd col": second_value,
                "3rd col": 0
            },
            "% change between": {
                "1st value": _self.pctchg_int*100,
                "2nd value": second_value,
                "3rd value": third_value,
                "1st col": "% Change",
                "1st col x": 100,
                "2nd col": second_value,
                "3rd col": third_value
            },
            "price vs ma": {
                "1st value": _self.curr_p,
                "2nd value": _self.curr_ma,
                "1st col": "Close",
                "1st col x": 1,
                "2nd col": 'ma',
                "3rd col": 0
            },
            "rsi vs selection": {
                "1st value": _self.curr_rsi,
                "2nd value": second_value,
                "1st col": "rsi",
                "1st col x": 1,
                "2nd col": second_value,
                "3rd col": 0
            },
            "ratio vs selection": {
                "1st value": _self.curr_p,
                "2nd value": second_value,
                "1st col": "Ratio",
                "1st col x": 1,
                "2nd col": second_value,
                "3rd col": 0
            },
            "ratio % change vs selection": {
                "1st value": _self.pctchg_int,
                "2nd value": second_value,
                "1st col": "Ratio % Chg",
                "1st col x": 1,
                "2nd col": second_value,
                "3rd col": 0
            }
        }

        # Initialize a variable to store the previous row's comparison result
        prev_comparison = False
        # Initialize an empty list to store the filtered rows
        filtered_rows = []
        # _self.db.to_csv('test.csv')
        for index, row in _self.db.iterrows():
            # Check if the current row meets the existing condition
            if isinstance(ref_dict[comparison_type]['1st col'], str):
                column1 = row[ref_dict[comparison_type]['1st col']]*ref_dict[comparison_type]['1st col x']
            else:
                column1 = ref_dict[comparison_type]['1st col']

            if isinstance(ref_dict[comparison_type]['2nd col'], str):
                column2 = row[ref_dict[comparison_type]['2nd col']]
            else:
                column2 = ref_dict[comparison_type]['2nd col']

            if isinstance(ref_dict[comparison_type]['3rd col'], str):
                column3 = row[ref_dict[comparison_type]['3rd col']]
            elif isinstance(third_value, (float, int)):
                column3 = third_value
            else: column3 = None
            
            if comparator =='Greater than':
                try:
                    current_comparison = column1 > column2
                except:
                    next
                
            elif comparator=='Less than':
                try:
                    current_comparison = column1 < column2
                except:
                    next
                
            elif comparator=='Between':
                try:
                    current_comparison = column2 <= column1 and column1 <= column3
                except:
                    next

            # Check if the previous row was not greater and the current row is greater
            if not prev_comparison and current_comparison:
                filtered_rows.append(row)
            
            # Update the previous comparison for the next iteration
            prev_comparison = current_comparison

        # Convert the filtered rows to a DataFrame
        filtered_database = pd.DataFrame(filtered_rows)

        sp500.append(filtered_database)
        ndx.append(filtered_database)
        rus2k.append(filtered_database)        

        return sp500, ndx, rus2k

    
class Generate_Yield():
    def __init__(self):
        self.db = None
        self.db_graph = None

        self.yield_ratio = None
        self.curr_yieldratio = None
        self.curr_ltyield = None
        self.curr_styield = None

        self.curr_yielddiff = None
        self.curr_yieldratio = None

    def generate_db(self, term_yield: str, start_date: str, end_date: str, interval: str = "1d"):
        """
        Provide the ticker for the term yield and generates a database; can either be:
        - 3 month: ^IRX
        - 10 year: ^TNX
        - 30 year: ^TYX
        """
        self.db = yf.download([term_yield], start_date, end_date, interval=interval)
        self.db_graph = self.db.drop(["Volume", 'Open', 'High', 'Low', 'Adj Close'], axis=1)
        self.db_graph['% Change'] = self.db['Close'].pct_change()

        return self.db_graph
    
    def generate_yield_ratio(self, start_date, end_date, interval, numerator: str, denominator: str):
        """
        Provide a numerator that is either 3 month (^IRX) or 10 year (^TNX) and a denominator that is either 10 year (^TNX) or 30 year (^TYX), returns a ratio between the numerator and denominator in a database.
        """
        # Generating Short and Long-Term databases
        self.num_yield, self.den_yield = self.generate_db(term_yield=numerator, start_date=start_date, end_date=end_date, interval=interval), self.generate_db(term_yield=denominator, start_date=start_date, end_date=end_date, interval=interval)
        self.num_yield.rename(columns={'Close': "Short Term Yield"}, inplace=True)
        self.den_yield.rename(columns={'Close': "Long Term Yield"}, inplace=True)

        # Calculates Yield Figures
        self.yield_ratio = pd.concat([self.num_yield, self.den_yield], axis=1)
        self.yield_ratio['Yield Ratio'] = self.yield_ratio['Short Term Yield']/self.yield_ratio['Long Term Yield']
        self.yield_ratio['Yield Ratio % Chg'] = self.yield_ratio['Yield Ratio'].pct_change()

        # Value for UI
        self.curr_yieldratio = round(self.yield_ratio['Yield Ratio'].iloc[-1],2)
        self.curr_ltyield = round(self.yield_ratio['Long Term Yield'].iloc[-1],2)
        self.curr_styield = round(self.yield_ratio['Short Term Yield'].iloc[-1],2)

    def metric_vs_selection(self, comparison_type:str, comparator:str, selected_value, sp500:pd.DataFrame, ndx:pd.DataFrame, rus2k:pd.DataFrame):
        type_dicts = {
            "ratio vs selection": {
                "1st value": self.curr_yieldratio,
                "2nd value": selected_value,
                "1st col": self.yield_ratio['Yield Ratio'],
                "2nd col": selected_value
            }
        }
        if comparator == 'Greater than':
            self.boolean_comp = type_dicts[comparison_type]['1st value'] > type_dicts[comparison_type]['2nd value']

            filtered_database = self.yield_ratio[type_dicts[comparison_type]['1st col'] > type_dicts[comparison_type]['2nd col']]

        elif comparator == 'Less than':
            self.boolean_comp = type_dicts[comparison_type]['1st value'] < type_dicts[comparison_type]['2nd value']

            filtered_database = self.yield_ratio[type_dicts[comparison_type]['1st col'] < type_dicts[comparison_type]['2nd col']]

        else:
            return "Check comparator value, should be either p greater or lower"

        sp500.append(filtered_database)
        ndx.append(filtered_database)
        rus2k.append(filtered_database)        

        return sp500, ndx, rus2k
