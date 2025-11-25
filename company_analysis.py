# ==================== company_analysis.py ====================
from data_extraction import extract_financial_data
from ratios import RatioCalculator

def analyze_company(ticker, tax_rate=0.21, period='quarterly'):
    """
    Analyze most recent period only (latest quarter or year).
    """
    print(f"\n{'='*70}")
    print(f"Analysis: {ticker} (Most Recent Period)")
    print('='*70)
    
    # Extract data - get most recent period (last row)
    df = extract_financial_data(ticker, period=period)
    latest = df.iloc[-1]  # Most recent period
    
    print(f"Period: {latest['date'].strftime('%Y-%m-%d')}")
    
    # Calculate ratios for latest period
    calc = RatioCalculator(latest)
    
    # Build report
    results = {
        'Profitability': {
            'ROE (%)': calc.roe() * 100,
            'ROA (%)': calc.roa() * 100,
            'Net Margin (%)': calc.net_margin() * 100,
        },
        'Liquidity': {
            'Current Ratio': calc.current_ratio(),
            'Quick Ratio': calc.quick_ratio(),
        },
        'Leverage': {
            'Debt/Equity': calc.debt_to_equity(),
        },
        'Cash Flow': {
            'FCF ($M)': calc.fcf(tax_rate) / 1e6,
        },
    }
    
    # Print report
    for category, metrics in results.items():
        print(f"\n{category}")
        print('-' * 50)
        for name, value in metrics.items():
            if isinstance(value, (int, float)):
                print(f"  {name:.<35} {value:>10.2f}")
            else:
                print(f"  {name:.<35} {value:>10}")
    
    return results