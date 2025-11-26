import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from data_extraction import extract_financial_data
from ratios import RatioCalculator
from dcf_analysis import (
    calculate_historical_growth, get_risk_free_rate,
    calculate_market_return, calculate_effective_tax_rate, calculate_wacc,
    dcf_valuation, print_dcf_report
)
import yfinance as yf

def calculate_growth_volatility(ticker, metric='fcf', tax_rate=0.21, period='annual'):
    """
    Calculate standard deviation of year-over-year growth rates.
    This measures how volatile the company's growth has been.
    """
    df = extract_financial_data(ticker, period=period)
    
    if len(df) < 3:
        return 0.10  # Default 10% volatility
    
    if metric == 'fcf':
        values = [RatioCalculator(row).fcf(tax_rate) for _, row in df.iterrows()]
    else:
        values = df[metric].values
    
    # Calculate year-over-year growth rates
    growth_rates = []
    for i in range(1, len(values)):
        if values[i-1] > 0 and values[i] > 0:
            growth = (values[i] - values[i-1]) / values[i-1]
            growth_rates.append(growth)
    
    if len(growth_rates) < 2:
        return 0.10
    
    return np.std(growth_rates)


def dcf_monte_carlo(ticker, n_simulations=10000, years=5, terminal_growth=0.03,
                    tax_rate=None, risk_free_rate=None, market_return=None):
    """
    Monte Carlo simulation of DCF valuation.
    Randomizes key parameters based on historical distributions.
    
    Returns: dict with probabilistic valuation results
    """
    # Auto-calculate base parameters
    if tax_rate is None:
        tax_rate = calculate_effective_tax_rate(ticker)
    
    if risk_free_rate is None:
        risk_free_rate = get_risk_free_rate()
    
    if market_return is None:
        market_return = calculate_market_return()
    
    # Get current price
    stock = yf.Ticker(ticker)
    info = stock.info
    current_price = info.get('currentPrice', 0)
    shares = info.get('sharesOutstanding', 1)
    
    # Calculate historical statistics
    historical_growth = calculate_historical_growth(ticker, metric='fcf', tax_rate=tax_rate)
    growth_volatility = calculate_growth_volatility(ticker, metric='fcf', tax_rate=tax_rate)
    
    # Get financial data for base FCF
    df = extract_financial_data(ticker, period='annual')
    latest = df.iloc[-1]
    calc = RatioCalculator(latest)
    base_fcf = calc.fcf(tax_rate)
    
    # Get base WACC
    base_wacc, _, _, beta = calculate_wacc(ticker, risk_free_rate, market_return, tax_rate)
    
    # Run Monte Carlo simulations
    fair_values = []
    simulation_params = []
    
    for i in range(n_simulations):
        # Randomize growth rate (normal distribution)
        sim_growth = np.random.normal(historical_growth, growth_volatility)
        sim_growth = max(0.01, min(sim_growth, 0.30))  # Cap between 1-30%
        
        # Randomize WACC (small variation based on market volatility)
        wacc_std = 0.015  # ±1.5% standard deviation
        sim_wacc = np.random.normal(base_wacc, wacc_std)
        sim_wacc = max(0.05, min(sim_wacc, 0.20))  # Cap between 5-20%
        
        # Randomize terminal growth (small variation)
        sim_terminal = np.random.normal(terminal_growth, 0.005)
        sim_terminal = max(0.01, min(sim_terminal, 0.05))  # Cap between 1-5%
        
        # Project FCF
        current_fcf = base_fcf
        projected_fcf = []
        for year in range(1, years + 1):
            fcf = current_fcf * ((1 + sim_growth) ** year)
            projected_fcf.append(fcf)
        
        # Calculate terminal value
        terminal_fcf = projected_fcf[-1] * (1 + sim_terminal)
        
        # Check if wacc > terminal growth (required for perpetuity formula)
        if sim_wacc <= sim_terminal:
            sim_wacc = sim_terminal + 0.02  # Ensure WACC > terminal growth
        
        terminal_value = terminal_fcf / (sim_wacc - sim_terminal)
        
        # Discount to present value
        pv_fcf = sum([fcf / ((1 + sim_wacc) ** (i+1)) for i, fcf in enumerate(projected_fcf)])
        pv_terminal = terminal_value / ((1 + sim_wacc) ** years)
        
        # Enterprise value
        enterprise_value = pv_fcf + pv_terminal
        
        # Equity value
        net_debt = latest['total_debt'] - latest['cash']
        equity_value = enterprise_value - net_debt
        
        # Fair value per share
        fair_value = equity_value / shares
        
        fair_values.append(fair_value)
        simulation_params.append({
            'growth': sim_growth,
            'wacc': sim_wacc,
            'terminal_growth': sim_terminal,
            'fair_value': fair_value
        })
    
    # Calculate statistics
    fair_values = np.array(fair_values)
    
    results = {
        'ticker': ticker,
        'current_price': current_price,
        'simulations': n_simulations,
        'mean_fair_value': np.mean(fair_values),
        'median_fair_value': np.median(fair_values),
        'std_fair_value': np.std(fair_values),
        'p10_fair_value': np.percentile(fair_values, 10),  # Pessimistic (10th percentile)
        'p25_fair_value': np.percentile(fair_values, 25),
        'p75_fair_value': np.percentile(fair_values, 75),
        'p90_fair_value': np.percentile(fair_values, 90),  # Optimistic (90th percentile)
        'prob_undervalued': np.mean(fair_values > current_price) * 100,
        'expected_upside': (np.mean(fair_values) - current_price) / current_price * 100,
        'median_upside': (np.median(fair_values) - current_price) / current_price * 100,
        'historical_growth': historical_growth * 100,
        'growth_volatility': growth_volatility * 100,
        'base_wacc': base_wacc * 100,
        'fair_values_array': fair_values,
        'simulation_params': simulation_params
    }
    
    # Recommendation based on probability
    prob = results['prob_undervalued']
    if prob > 80:
        results['recommendation'] = 'STRONG BUY'
    elif prob > 65:
        results['recommendation'] = 'BUY'
    elif prob > 50:
        results['recommendation'] = 'HOLD'
    elif prob > 35:
        results['recommendation'] = 'SELL'
    else:
        results['recommendation'] = 'STRONG SELL'
    
    return results


def print_monte_carlo_report(results):
    """Pretty print Monte Carlo DCF results"""
    print(f"\n{'='*70}")
    print(f"MONTE CARLO DCF ANALYSIS: {results['ticker']}")
    print(f"Simulations: {results['simulations']:,}")
    print('='*70)
    
    print(f"\nCurrent Market Price: ${results['current_price']:.2f}")
    
    print(f"\nProbabilistic Fair Value Estimates")
    print('-' * 70)
    print(f"  Mean Fair Value.................... ${results['mean_fair_value']:>10.2f}")
    print(f"  Median Fair Value.................. ${results['median_fair_value']:>10.2f}")
    print(f"  Standard Deviation................. ${results['std_fair_value']:>10.2f}")
    
    print(f"\nConfidence Intervals")
    print('-' * 70)
    print(f"  10th Percentile (Pessimistic)...... ${results['p10_fair_value']:>10.2f}")
    print(f"  25th Percentile.................... ${results['p25_fair_value']:>10.2f}")
    print(f"  75th Percentile.................... ${results['p75_fair_value']:>10.2f}")
    print(f"  90th Percentile (Optimistic)....... ${results['p90_fair_value']:>10.2f}")
    print(f"  80% Confidence Range............... ${results['p10_fair_value']:.2f} - ${results['p90_fair_value']:.2f}")
    
    print(f"\nProbabilistic Assessment")
    print('-' * 70)
    print(f"  Probability Undervalued............ {results['prob_undervalued']:>10.1f}%")
    print(f"  Expected Upside (Mean)............. {results['expected_upside']:>10.1f}%")
    print(f"  Expected Upside (Median)........... {results['median_upside']:>10.1f}%")
    
    print(f"\nHistorical Parameters Used")
    print('-' * 70)
    print(f"  Historical FCF Growth (Mean)....... {results['historical_growth']:>10.1f}%")
    print(f"  Growth Volatility (Std Dev)........ {results['growth_volatility']:>10.1f}%")
    print(f"  Base WACC.......................... {results['base_wacc']:>10.1f}%")
    
    print(f"\nRecommendation: {results['recommendation']}")
    print('='*70)
    print()


def plot_monte_carlo_distribution(results):
    """
    Plot distribution of fair values from Monte Carlo simulation.
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    fair_values = results['fair_values_array']
    current_price = results['current_price']
    
    # Plot 1: Histogram of fair values
    ax1 = axes[0]
    ax1.hist(fair_values, bins=100, alpha=0.7, color='steelblue', edgecolor='black')
    ax1.axvline(current_price, color='red', linestyle='--', linewidth=2, label=f'Current Price: ${current_price:.2f}')
    ax1.axvline(results['mean_fair_value'], color='green', linestyle='-', linewidth=2, label=f'Mean Fair Value: ${results["mean_fair_value"]:.2f}')
    ax1.axvline(results['p10_fair_value'], color='orange', linestyle=':', linewidth=1.5, label=f'10th %ile: ${results["p10_fair_value"]:.2f}')
    ax1.axvline(results['p90_fair_value'], color='orange', linestyle=':', linewidth=1.5, label=f'90th %ile: ${results["p90_fair_value"]:.2f}')
    
    ax1.set_xlabel('Fair Value per Share ($)', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.set_title(f'{results["ticker"]} - Distribution of Fair Values ({results["simulations"]:,} Simulations)', 
                  fontsize=14, fontweight='bold')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Cumulative probability
    ax2 = axes[1]
    sorted_values = np.sort(fair_values)
    cumulative_prob = np.arange(1, len(sorted_values) + 1) / len(sorted_values) * 100
    
    ax2.plot(sorted_values, cumulative_prob, linewidth=2, color='steelblue')
    ax2.axvline(current_price, color='red', linestyle='--', linewidth=2, label=f'Current Price: ${current_price:.2f}')
    ax2.axhline(results['prob_undervalued'], color='green', linestyle=':', linewidth=1.5, 
                label=f'P(Undervalued) = {results["prob_undervalued"]:.1f}%')
    
    ax2.set_xlabel('Fair Value per Share ($)', fontsize=12)
    ax2.set_ylabel('Cumulative Probability (%)', fontsize=12)
    ax2.set_title(f'{results["ticker"]} - Cumulative Probability Distribution', fontsize=14, fontweight='bold')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def monte_carlo_comparison(tickers, n_simulations=10000):
    """
    Compare Monte Carlo DCF results across multiple companies.
    """
    comparison = {}
    
    for ticker in tickers:
        try:
            results = dcf_monte_carlo(ticker, n_simulations=n_simulations)
            comparison[ticker] = {
                'Current Price': results['current_price'],
                'Mean Fair Value': results['mean_fair_value'],
                'Median Fair Value': results['median_fair_value'],
                'P(Undervalued) %': results['prob_undervalued'],
                'Expected Upside %': results['expected_upside'],
                '80% CI Lower': results['p10_fair_value'],
                '80% CI Upper': results['p90_fair_value'],
                'Recommendation': results['recommendation']
            }
        except Exception as e:
            print(f"Error with {ticker}: {e}")
            continue
    
    df = pd.DataFrame(comparison).T
    return df.sort_values('P(Undervalued) %', ascending=False)