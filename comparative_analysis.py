from data_extraction import extract_financial_data
from ratios import RatioCalculator
import pandas as pd

def compare_companies(tickers, tax_rate=0.21, period='quarterly'):
    """
    Compare multiple companies using most recent period data.
    Returns DataFrame with companies as rows, metrics as columns.
    """
    comparison = {}
    
    for ticker in tickers:
        try:
            df = extract_financial_data(ticker, period=period)
            latest = df.iloc[-1]  # Most recent period
            calc = RatioCalculator(latest)
            
            comparison[ticker] = {
                'ROE (%)': calc.roe() * 100,
                'ROA (%)': calc.roa() * 100,
                'Net Margin (%)': calc.net_margin() * 100,
                'Current Ratio': calc.current_ratio(),
                'Quick Ratio': calc.quick_ratio(),
                'Debt/Equity': calc.debt_to_equity(),
                'FCF ($M)': calc.fcf(tax_rate) / 1e6,
            }
        except Exception as e:
            print(f"Error with {ticker}: {e}")
            continue
    
    df = pd.DataFrame(comparison).T
    return df