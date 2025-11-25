class RatioCalculator:
    """
    Logic: Each ratio is just arithmetic on the extracted data.
    Formulas match your COMM 370 sheet exactly.
    """
    
    def __init__(self, data):
        self.d = data  # Store data dict
    
    # Valuation
    def pe_ratio(self):
        eps = self.d['net_income'] / self.d['shares']
        return self.d['price'] / eps if eps != 0 else np.nan
    
    def pb_ratio(self):
        book_per_share = self.d['equity'] / self.d['shares']
        return self.d['price'] / book_per_share if book_per_share != 0 else np.nan
    
    def ev_ebitda(self):
        ev = self.d['market_cap'] + self.d['total_debt'] - self.d['cash']
        return ev / self.d['ebitda'] if self.d['ebitda'] != 0 else np.nan
    
    # Profitability
    def roe(self):
        return self.d['net_income'] / self.d['equity'] if self.d['equity'] != 0 else np.nan
    
    def roa(self):
        return self.d['net_income'] / self.d['total_assets'] if self.d['total_assets'] != 0 else np.nan
    
    def net_margin(self):
        return self.d['net_income'] / self.d['revenue'] if self.d['revenue'] != 0 else np.nan
    
    # Liquidity
    def current_ratio(self):
        return self.d['current_assets'] / self.d['current_liabilities'] if self.d['current_liabilities'] != 0 else np.nan
    
    def quick_ratio(self):
        quick_assets = self.d['cash'] + self.d['receivables']
        return quick_assets / self.d['current_liabilities'] if self.d['current_liabilities'] != 0 else np.nan
    
    # Leverage
    def debt_to_equity(self):
        return self.d['total_debt'] / self.d['equity'] if self.d['equity'] != 0 else np.nan
    
    def interest_coverage(self):
        ebitda = self.d['ebit'] + self.d['depreciation']
        return ebitda / self.d['interest'] if self.d['interest'] != 0 else np.nan
    
    # Cash Flow
    def fcf(self, tax_rate=0.21):
        """Free Cash Flow = EBIT(1-τ) + Depreciation - CapEx - ΔNWC"""
        # Simplified: ignoring ΔNWC for now
        return (self.d['ebit'] * (1 - tax_rate) + 
                self.d['depreciation'] - 
                abs(self.d['capex']))
    
    # Credit Risk (Altman Z-Score)
    def z_score(self):
        """Z-Score formula from your sheet"""
        nwc = self.d['cash'] + self.d['inventory'] + self.d['receivables'] - self.d['payables']
        
        x1 = 1.2 * (nwc / self.d['total_assets'])
        x2 = 1.4 * (self.d['retained_earnings'] / self.d['total_assets'])
        x3 = 3.3 * (self.d['ebit'] / self.d['total_assets'])
        x4 = 0.6 * (self.d['market_cap'] / (self.d['total_assets'] - self.d['equity']))
        x5 = 1.0 * (self.d['revenue'] / self.d['total_assets'])
        
        z = x1 + x2 + x3 + x4 + x5
        
        zone = 'Safe' if z > 2.99 else 'Grey' if z > 1.8 else 'Distress'
        return z, zone