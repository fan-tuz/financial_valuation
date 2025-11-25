import yfinance as yf
import pandas as pd

def extract_financial_data(ticker, period='quarterly'):
    """
    Returns DataFrame with quarterly or annual financial data.
    
    Args:
        ticker: Stock ticker
        period: 'quarterly' or 'annual'
    """
    stock = yf.Ticker(ticker)
    
    # Select quarterly or annual data
    if period == 'quarterly':
        income = stock.quarterly_income_stmt
        balance = stock.quarterly_balance_sheet
        cashflow = stock.quarterly_cashflow
    else:
        income = stock.income_stmt
        balance = stock.balance_sheet
        cashflow = stock.cashflow
    
    def get(df, key, col_idx):
        try:
            val = df.loc[key].iloc[col_idx]
            return float(val) if pd.notna(val) else 0
        except:
            return 0
    
    # Build list of dictionaries (one per period)
    data_list = []
    for i in range(len(income.columns)):
        date = income.columns[i]
        data_list.append({
            'date': date,
            'revenue': get(income, 'Total Revenue', i),
            'cogs': get(income, 'Cost Of Revenue', i),
            'ebit': get(income, 'EBIT', i),
            'ebitda': get(income, 'EBITDA', i),
            'depreciation': get(income, 'Reconciled Depreciation', i),
            'interest': abs(get(income, 'Interest Expense', i)),
            'net_income': get(income, 'Net Income', i),
            'cash': get(balance, 'Cash And Cash Equivalents', i),
            'receivables': get(balance, 'Accounts Receivable', i),
            'inventory': get(balance, 'Inventory', i),
            'current_assets': get(balance, 'Current Assets', i),
            'total_assets': get(balance, 'Total Assets', i),
            'payables': get(balance, 'Accounts Payable', i),
            'current_liabilities': get(balance, 'Current Liabilities', i),
            'total_debt': get(balance, 'Total Debt', i),
            'equity': get(balance, 'Stockholders Equity', i),
            'retained_earnings': get(balance, 'Retained Earnings', i),
            'operating_cf': get(cashflow, 'Operating Cash Flow', i),
            'capex': get(cashflow, 'Capital Expenditure', i),
        })
    
    df = pd.DataFrame(data_list)
    return df.sort_values('date').reset_index(drop=True)