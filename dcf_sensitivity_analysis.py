import numpy as np
import pandas as pd
import yfinance as yf
from data_extraction import extract_financial_data
from ratios import RatioCalculator
from dcf_analysis import (
    calculate_historical_growth, get_risk_free_rate,
    calculate_market_return, calculate_effective_tax_rate, calculate_wacc,
    dcf_valuation, print_dcf_report
)

def dcf_sensitivity_analysis(ticker, tax_rate=None, risk_free_rate=None, market_return=None):
    """
    Run DCF valuation under Bear, Base, and Bull scenarios.
    Uses data-driven parameters when possible.
    
    Returns: DataFrame with scenarios and sensitivity matrix
    """
    stock = yf.Ticker(ticker)
    current_price = stock.info.get('currentPrice', 0)
    
    # Calculate data-driven parameters
    historical_fcf_growth = calculate_historical_growth(ticker, metric='fcf', tax_rate=tax_rate or 0.21)
    historical_revenue_growth = calculate_historical_growth(ticker, metric='revenue')
    
    if tax_rate is None:
        tax_rate = calculate_effective_tax_rate(ticker)
    
    if risk_free_rate is None:
        risk_free_rate = get_risk_free_rate()
    
    # Define scenarios based on historical growth
    scenarios = {
        'Bear': {
            'growth_rate': max(0.02, historical_fcf_growth * 0.5),  # 50% of historical
            'terminal_growth': 0.02,
            'description': 'Conservative (50% historical growth)'
        },
        'Base': {
            'growth_rate': max(0.03, historical_fcf_growth * 0.8),  # 80% of historical
            'terminal_growth': 0.03,
            'description': 'Realistic (80% historical growth)'
        },
        'Bull': {
            'growth_rate': max(0.05, historical_fcf_growth * 1.2),  # 120% of historical
            'terminal_growth': 0.04,
            'description': 'Optimistic (120% historical growth)'
        }
    }
    
    # Run DCF for each scenario
    results = {}
    for name, params in scenarios.items():
        val = dcf_valuation(
            ticker, 
            growth_rate=params['growth_rate'],
            terminal_growth=params['terminal_growth'],
            risk_free_rate=risk_free_rate,
            tax_rate=tax_rate
        )
        results[name] = {
            'fair_value': val['fair_value'],
            'upside_pct': val['upside_pct'],
            'growth_rate': params['growth_rate'] * 100,
            'terminal_growth': params['terminal_growth'] * 100,
            'description': params['description']
        }
    
    # Create summary DataFrame
    summary = pd.DataFrame(results).T
    summary['current_price'] = current_price
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"DCF SENSITIVITY ANALYSIS: {ticker}")
    print('='*70)
    print(f"\nCurrent Price: ${current_price:.2f}")
    print(f"\nData-Driven Assumptions:")
    print(f"  Historical FCF Growth (CAGR)....... {historical_fcf_growth*100:>6.1f}%")
    print(f"  Historical Revenue Growth (CAGR)... {historical_revenue_growth*100:>6.1f}%")
    print(f"  Effective Tax Rate................. {tax_rate*100:>6.1f}%")
    print(f"  Risk-Free Rate (10Y Treasury)...... {risk_free_rate*100:>6.1f}%")
    
    print(f"\n{'Scenario':<12} {'Growth':<10} {'Term.Grw':<10} {'Fair Value':<12} {'Upside':<10}")
    print('-' * 70)
    for name in ['Bear', 'Base', 'Bull']:
        r = results[name]
        print(f"{name:<12} {r['growth_rate']:>6.1f}%    {r['terminal_growth']:>6.1f}%    "
              f"${r['fair_value']:>8.2f}     {r['upside_pct']:>6.1f}%")
    
    # Investment decision
    print(f"\nInvestment Decision:")
    print('-' * 70)
    if results['Bear']['upside_pct'] > 10:
        decision = "STRONG BUY - Positive upside even in bear case"
    elif results['Base']['upside_pct'] > 15:
        decision = "BUY - Good upside in base case"
    elif results['Bull']['upside_pct'] > 10:
        decision = "HOLD - Only attractive in bull case"
    else:
        decision = "AVOID - Limited upside across scenarios"
    
    print(f"  {decision}")
    print()
    
    return summary

def dcf_comparison(tickers, tax_rate=None):
    """
    Compare DCF valuations across multiple companies.
    All parameters are data-driven by default.
    Returns DataFrame with fair values and upside for each.
    """
    comparison = {}
    
    for ticker in tickers:
        try:
            # All parameters auto-calculated
            results = dcf_valuation(ticker, tax_rate=tax_rate)
            
            comparison[ticker] = {
                'Current Price': results['current_price'],
                'Fair Value': results['fair_value'],
                'Upside (%)': results['upside_pct'],
                'Growth Rate (%)': results['growth_rate'],
                'WACC (%)': results['wacc']
            }
        except Exception as e:
            print(f"Error with {ticker}: {e}")
            continue
    
    df = pd.DataFrame(comparison).T
    return df.sort_values('Upside (%)', ascending=False)