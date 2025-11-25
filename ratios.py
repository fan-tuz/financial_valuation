import numpy as np
import pandas as pd

class RatioCalculator:
    """Calculates ratios for a single period (one row of DataFrame)"""
    
    def __init__(self, row):
        self.d = row
    
    def roe(self):
        return self.d['net_income'] / self.d['equity'] if self.d['equity'] != 0 else np.nan
    
    def roa(self):
        return self.d['net_income'] / self.d['total_assets'] if self.d['total_assets'] != 0 else np.nan
    
    def net_margin(self):
        return self.d['net_income'] / self.d['revenue'] if self.d['revenue'] != 0 else np.nan
    
    def current_ratio(self):
        return self.d['current_assets'] / self.d['current_liabilities'] if self.d['current_liabilities'] != 0 else np.nan
    
    def quick_ratio(self):
        quick_assets = self.d['cash'] + self.d['receivables']
        return quick_assets / self.d['current_liabilities'] if self.d['current_liabilities'] != 0 else np.nan
    
    def debt_to_equity(self):
        return self.d['total_debt'] / self.d['equity'] if self.d['equity'] != 0 else np.nan
    
    def fcf(self, tax_rate=0.21):
        return (self.d['ebit'] * (1 - tax_rate) + 
                self.d['depreciation'] - 
                abs(self.d['capex']))

def calculate_ratios_timeseries(df, tax_rate=0.21):
    """
    Calculate ratios for entire DataFrame (all periods).
    Returns new DataFrame with ratios.
    """
    ratios_list = []
    
    for _, row in df.iterrows():
        calc = RatioCalculator(row)
        ratios_list.append({
            'date': row['date'],
            'roe': calc.roe(),
            'roa': calc.roa(),
            'net_margin': calc.net_margin(),
            'current_ratio': calc.current_ratio(),
            'quick_ratio': calc.quick_ratio(),
            'debt_to_equity': calc.debt_to_equity(),
            'fcf': calc.fcf(tax_rate) / 1e6,  # in millions
        })
    
    return pd.DataFrame(ratios_list)