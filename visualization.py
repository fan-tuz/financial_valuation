import matplotlib.pyplot as plt
from data_extraction import extract_financial_data

def plot_metrics(ticker, metrics=[], period='quarterly'):
    """
    Plot evolution of raw financial metrics over time.
    
    Args:
        ticker: Stock ticker
        metrics: List of metric names from financial statements
        period: 'quarterly' or 'annual'
    """
    df = extract_financial_data(ticker, period=period)
    
    n_metrics = len(metrics)
    fig, axes = plt.subplots(n_metrics, 1, figsize=(14, 4*n_metrics))
    
    if n_metrics == 1:
        axes = [axes]
    
    for ax, metric in zip(axes, metrics):
        ax.plot(df['date'], df[metric] / 1e9, marker='o', linewidth=2, markersize=4)
        ax.set_title(f'{ticker} - {metric.replace("_", " ").title()} ({period.title()})', 
                     fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Billions ($)')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()

def plot_ratios(ticker, ratios=[], period='quarterly', tax_rate=0.21):
    """
    Plot evolution of financial ratios over time.
    
    Args:
        ticker: Stock ticker
        ratios: List of ratio names (e.g., ['roe', 'roa', 'current_ratio'])
        period: 'quarterly' or 'annual'
        tax_rate: Tax rate for FCF calculation
    """
    df = extract_financial_data(ticker, period=period)
    ratios_df = calculate_ratios_timeseries(df, tax_rate=tax_rate)
    
    n_ratios = len(ratios)
    fig, axes = plt.subplots(n_ratios, 1, figsize=(14, 4*n_ratios))
    
    if n_ratios == 1:
        axes = [axes]
    
    for ax, ratio in zip(axes, ratios):
        ax.plot(ratios_df['date'], ratios_df[ratio], marker='o', linewidth=2, markersize=4)
        ax.set_title(f'{ticker} - {ratio.replace("_", " ").upper()} ({period.title()})', 
                     fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Ratio Value')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()

def plot_comparison(tickers, metrics=[], period='quarterly', tax_rate=0.21):
    """
    Plot side-by-side comparison of metrics across multiple companies.
    Shows time series for each company on the same chart.
    
    Args:
        tickers: List of stock tickers
        metrics: List of metrics to compare ('roe', 'roa', 'net_margin', 'current_ratio', 'debt_to_equity')
        period: 'quarterly' or 'annual'
        tax_rate: Tax rate for FCF calculation
    """
    from ratios import calculate_ratios_timeseries
    
    # Collect data for all companies
    all_data = {}
    for ticker in tickers:
        try:
            df = extract_financial_data(ticker, period=period)
            ratios_df = calculate_ratios_timeseries(df, tax_rate=tax_rate)
            all_data[ticker] = ratios_df
        except Exception as e:
            print(f"Error with {ticker}: {e}")
            continue
    
    # Create plots
    n_metrics = len(metrics)
    fig, axes = plt.subplots(n_metrics, 1, figsize=(14, 4*n_metrics))
    
    if n_metrics == 1:
        axes = [axes]
    
    for ax, metric in zip(axes, metrics):
        for ticker, ratios_df in all_data.items():
            # Convert percentages for display
            if metric in ['roe', 'roa', 'net_margin']:
                values = ratios_df[metric] * 100
                ylabel = 'Percentage (%)'
            else:
                values = ratios_df[metric]
                ylabel = 'Ratio Value'
            
            ax.plot(ratios_df['date'], values, marker='o', linewidth=2, 
                   markersize=4, label=ticker)
        
        ax.set_title(f'{metric.replace("_", " ").upper()} Comparison ({period.title()})', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        #ax.set_ylabel(ylabel)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.show()