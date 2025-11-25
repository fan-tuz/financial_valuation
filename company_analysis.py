from data_extraction import extract_financial_data
from ratios import RatioCalculator

def analyze_company(ticker, tax_rate=0.21):
    """
    Complete workflow: Extract → Calculate → Report
    """
    print(f"\n{'='*70}")
    print(f"Analysis: {ticker}")
    print('='*70)
    
    # Step 1: Extract data
    data = extract_financial_data(ticker)
    
    # Step 2: Calculate ratios
    calc = RatioCalculator(data)
    
    # Step 3: Build report
    results = {
        'Valuation': {
            'P/E Ratio': calc.pe_ratio(),
            'P/B Ratio': calc.pb_ratio(),
            'EV/EBITDA': calc.ev_ebitda(),
        },
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
            'Interest Coverage': calc.interest_coverage(),
        },
        'Cash Flow': {
            'FCF ($M)': calc.fcf(tax_rate) / 1e6,
        },
    }
    
    # Add Z-Score
    z, zone = calc.z_score()
    results['Credit Risk'] = {
        'Z-Score': z,
        'Risk Zone': zone,
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
    
    return results_df