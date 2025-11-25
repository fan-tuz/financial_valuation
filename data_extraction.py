import yfinance as yf
import pandas as pd
import numpy as np

def extract_financial_data(ticker):
    """
    Core logic: yfinance returns DataFrames where:
    - Rows = financial line items
    - Columns = time periods (most recent = column 0)
    - Access: df.loc['Item Name'].iloc[0]
    """
    stock = yf.Ticker(ticker)
    
    # Three main DataFrames
    income = stock.income_stmt
    balance = stock.balance_sheet
    cashflow = stock.cashflow
    info = stock.info               # Real-time data & metadata (dict)
    
    # Safe extraction function to handle missing keys
    def get(df, key, default=0):
        try:
            val = df.loc[key].iloc[0]
            return float(val) if pd.notna(val) else default
        except:
            return default
    
    # Build dictionary with all needed data
    data = {
        # From info dict (current market data)
        'price': info.get('currentPrice', 0),
        'shares': info.get('sharesOutstanding', 0),
        'market_cap': info.get('marketCap', 0),
        
        # From income statement
        'revenue': get(income, 'Total Revenue'),
        'cogs': get(income, 'Cost Of Revenue'),
        'ebit': get(income, 'EBIT'),
        'ebitda': get(income, 'EBITDA'),
        'depreciation': get(income, 'Reconciled Depreciation'),
        'interest': abs(get(income, 'Interest Expense')),
        'net_income': get(income, 'Net Income'),
        
        # From balance sheet
        'cash': get(balance, 'Cash And Cash Equivalents'),
        'receivables': get(balance, 'Accounts Receivable'),
        'inventory': get(balance, 'Inventory'),
        'current_assets': get(balance, 'Current Assets'),
        'total_assets': get(balance, 'Total Assets'),
        'payables': get(balance, 'Accounts Payable'),
        'current_liabilities': get(balance, 'Current Liabilities'),
        'total_debt': get(balance, 'Total Debt'),
        'equity': get(balance, 'Stockholders Equity'),
        'retained_earnings': get(balance, 'Retained Earnings'),
        
        # From cash flow statement
        'operating_cf': get(cashflow, 'Operating Cash Flow'),
        'capex': get(cashflow, 'Capital Expenditure'),
        'dividends': abs(get(cashflow, 'Cash Dividends Paid')),
    }
    
    return data