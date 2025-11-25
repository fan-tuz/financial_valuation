from data_extraction import extract_financial_data
from ratios import RatioCalculator
import pandas as pd

def compare_companies(tickers, tax_rate=0.21):
    """
    Logic: Run analysis on multiple companies, aggregate results
    """
    comparison = {}
    
    for ticker in tickers:
        try:
            data = extract_financial_data(ticker)
            calc = RatioCalculator(data)
            
            comparison[ticker] = {
                'P/E': calc.pe_ratio(),
                'ROE': calc.roe(),
                'Current Ratio': calc.current_ratio(),
                'Debt/Equity': calc.debt_to_equity(),
                'Z-Score': calc.z_score()[0],
                'FCF ($M)': calc.fcf(tax_rate) / 1e6,
            }
        except Exception as e:
            print(f"Error with {ticker}: {e}")
            continue
    
    # Convert to DataFrame for easy viewing
    df = pd.DataFrame(comparison).T
    return df