import numpy as np
import pandas as pd
import yfinance as yf
from data_extraction import extract_financial_data
from ratios import RatioCalculator

def calculate_historical_growth(ticker, metric='fcf', tax_rate=0.21, period='annual'):
    """
    Calculate historical CAGR for a given metric.
    Returns: CAGR as decimal (e.g., 0.08 = 8%)
    """
    df = extract_financial_data(ticker, period=period)
    
    if len(df) < 2:
        return 0.05  # Default if insufficient data
    
    if metric == 'fcf':
        values = [RatioCalculator(row).fcf(tax_rate) for _, row in df.iterrows()]
    else:
        values = df[metric].values
    
    # Filter out zeros and negatives for CAGR calculation
    values = [v for v in values if v > 0]
    
    if len(values) < 2:
        return 0.05  # Default
    
    # CAGR = (End/Start)^(1/years) - 1
    years = len(values) - 1
    cagr = (values[-1] / values[0]) ** (1/years) - 1
    
    return cagr


def get_risk_free_rate():
    """Get current 10-year Treasury yield"""
    try:
        treasury = yf.Ticker('^TNX')
        rate = treasury.info.get('regularMarketPrice', 4.0) / 100
        return rate
    except:
        return 0.04  # Default 4%


def calculate_market_return(years=10):
    """Calculate historical S&P 500 return (CAGR)"""
    try:
        sp500 = yf.Ticker('^GSPC')
        hist = sp500.history(period=f'{years}y')
        start_price = hist['Close'].iloc[0]
        end_price = hist['Close'].iloc[-1]
        cagr = (end_price / start_price) ** (1/years) - 1
        return cagr
    except:
        return 0.10  # Default 10%


def calculate_effective_tax_rate(ticker):
    """Calculate company's effective tax rate from financial statements"""
    df = extract_financial_data(ticker, period='annual')
    latest = df.iloc[-1]
    
    ebit = latest['ebit']
    net_income = latest['net_income']
    interest = latest['interest']
    
    if ebit <= 0:
        return 0.21  # Default
    
    # Implied tax = (EBIT - Interest - Net Income) / (EBIT - Interest)
    taxable_income = ebit - interest
    if taxable_income <= 0:
        return 0.21
    
    tax_paid = taxable_income - net_income
    effective_rate = tax_paid / taxable_income
    
    # Cap between 0-40%
    return max(0, min(effective_rate, 0.40))

def calculate_wacc(ticker, risk_free_rate=None, market_return=None, tax_rate=None):
    """
    Calculate WACC using CAPM with data-driven defaults.
    WACC = (E/V) * r_e + (D/V) * r_d * (1-τ)
    where r_e = r_f + β * (E[R_m] - r_f)
    """
    # Auto-calculate parameters if not provided
    if risk_free_rate is None:
        risk_free_rate = get_risk_free_rate()
    
    if market_return is None:
        market_return = calculate_market_return()
    
    if tax_rate is None:
        tax_rate = calculate_effective_tax_rate(ticker)
    
    stock = yf.Ticker(ticker)
    info = stock.info
    
    # Get market data
    beta = info.get('beta', 1.0)
    market_cap = info.get('marketCap', 0)
    
    # Get debt from balance sheet
    df = extract_financial_data(ticker, period='annual')
    latest = df.iloc[-1]
    total_debt = latest['total_debt']
    
    # Calculate cost of equity (CAPM)
    cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)
    
    # Calculate cost of debt (approximation: interest / debt)
    cost_of_debt = latest['interest'] / total_debt if total_debt > 0 else 0.05
    
    # Calculate WACC
    total_value = market_cap + total_debt
    weight_equity = market_cap / total_value if total_value > 0 else 1
    weight_debt = total_debt / total_value if total_value > 0 else 0
    
    wacc = weight_equity * cost_of_equity + weight_debt * cost_of_debt * (1 - tax_rate)
    
    return wacc, cost_of_equity, cost_of_debt, beta


def dcf_valuation(ticker, growth_rate=None, terminal_growth=0.03, 
                  risk_free_rate=None, market_return=None, tax_rate=None, years=5):
    """
    DCF Valuation using Free Cash Flow projection with data-driven defaults.
    
    Steps:
    1. Calculate historical FCF
    2. Project FCF for next 5 years with growth rate
    3. Calculate terminal value
    4. Discount everything with WACC
    5. Calculate equity value per share
    
    Returns: dict with valuation results
    """
    # Auto-calculate parameters if not provided
    if tax_rate is None:
        tax_rate = calculate_effective_tax_rate(ticker)
    
    if risk_free_rate is None:
        risk_free_rate = get_risk_free_rate()
    
    if market_return is None:
        market_return = calculate_market_return()
    
    if growth_rate is None:
        # Use 80% of historical FCF growth as base case
        historical_growth = calculate_historical_growth(ticker, metric='fcf', tax_rate=tax_rate)
        growth_rate = max(0.03, historical_growth * 0.8)
    
    stock = yf.Ticker(ticker)
    info = stock.info
    
    # Get financial data
    df = extract_financial_data(ticker, period='annual')
    latest = df.iloc[-1]
    calc = RatioCalculator(latest)
    
    # Calculate current FCF
    current_fcf = calc.fcf(tax_rate)
    
    # Get shares outstanding
    shares = info.get('sharesOutstanding', 1)
    current_price = info.get('currentPrice', 0)
    
    # Calculate WACC
    wacc, cost_of_equity, cost_of_debt, beta = calculate_wacc(
        ticker, risk_free_rate, market_return, tax_rate
    )
    
    # Project FCF for next years
    projected_fcf = []
    for year in range(1, years + 1):
        fcf = current_fcf * ((1 + growth_rate) ** year)
        projected_fcf.append(fcf)
    
    # Calculate Terminal Value (perpetuity growth model)
    terminal_fcf = projected_fcf[-1] * (1 + terminal_growth)
    terminal_value = terminal_fcf / (wacc - terminal_growth)
    
    # Discount all cash flows to present value
    pv_fcf = sum([fcf / ((1 + wacc) ** (i+1)) for i, fcf in enumerate(projected_fcf)])
    pv_terminal = terminal_value / ((1 + wacc) ** years)
    
    # Enterprise Value = PV of projected FCF + PV of terminal value
    enterprise_value = pv_fcf + pv_terminal
    
    # Equity Value = Enterprise Value - Net Debt
    net_debt = latest['total_debt'] - latest['cash']
    equity_value = enterprise_value - net_debt
    
    # Value per share
    fair_value_per_share = equity_value / shares
    
    # Calculate upside/downside
    upside_pct = ((fair_value_per_share - current_price) / current_price) * 100
    
    results = {
        'ticker': ticker,
        'current_price': current_price,
        'fair_value': fair_value_per_share,
        'upside_pct': upside_pct,
        'wacc': wacc * 100,
        'beta': beta,
        'growth_rate': growth_rate * 100,
        'risk_free_rate': risk_free_rate * 100,
        'market_return': market_return * 100,
        'tax_rate': tax_rate * 100,
        'current_fcf_millions': current_fcf / 1e6,
        'enterprise_value_millions': enterprise_value / 1e6,
        'equity_value_millions': equity_value / 1e6,
    }
    
    return results


def print_dcf_report(results):
    """Pretty print DCF valuation results"""
    print(f"\n{'='*70}")
    print(f"DCF VALUATION: {results['ticker']}")
    print('='*70)
    
    print(f"\nValuation Summary")
    print('-' * 50)
    print(f"  Current Price...................... ${results['current_price']:>10.2f}")
    print(f"  Fair Value (DCF)................... ${results['fair_value']:>10.2f}")
    print(f"  Upside/(Downside).................. {results['upside_pct']:>10.1f}%")
    
    print(f"\nData-Driven Assumptions")
    print('-' * 50)
    print(f"  Growth Rate (5Y)................... {results['growth_rate']:>10.2f}%")
    print(f"  WACC............................... {results['wacc']:>10.2f}%")
    print(f"  Beta............................... {results['beta']:>10.2f}")
    print(f"  Risk-Free Rate (10Y Treasury)...... {results['risk_free_rate']:>10.2f}%")
    print(f"  Market Return (S&P 500 10Y)........ {results['market_return']:>10.2f}%")
    print(f"  Effective Tax Rate................. {results['tax_rate']:>10.2f}%")
    
    print(f"\nValue Breakdown")
    print('-' * 50)
    print(f"  Current FCF........................ ${results['current_fcf_millions']:>10.0f}M")
    print(f"  Enterprise Value................... ${results['enterprise_value_millions']:>10.0f}M")
    print(f"  Equity Value....................... ${results['equity_value_millions']:>10.0f}M")
    print()