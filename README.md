# Corporate Valuation & Financial Analysis Framework

**Probabilistic DCF valuation system with Monte Carlo simulation for equity analysis**

Developed alongside Corporate Finance coursework, University of British Columbia (Canada)

---

## Overview

This project implements a comprehensive framework for equity valuation combining deterministic Discounted Cash Flow (DCF) analysis with Monte Carlo simulation to quantify valuation uncertainty. Built as a practical application of financial theory, the system moves beyond traditional point estimates to provide probability distributions of fair values, enabling more informed investment decisions under uncertainty.

### Key Innovation

Traditional DCF models produce single-point fair value estimates that ignore parameter uncertainty. This framework recognizes that **growth rates, discount rates, and terminal values are inherently uncertain** and uses stochastic simulation to generate probability distributions of outcomes, answering critical questions like:
- What is the probability this stock is undervalued?
- What is the 80% confidence interval for fair value?
- What returns can I expect under different scenarios?

---

## Motivation & Learning Objectives

### Academic Context
Developed as an extension of Corporate Finance coursework focusing on:
- **Valuation Theory**: DCF methodology, WACC calculation, terminal value estimation
- **Stochastic Processes**: Modeling growth rate uncertainty with normal distributions
- **Monte Carlo Methods**: Simulating thousands of scenarios to capture parameter uncertainty
- **Statistical Inference**: Probability distributions, confidence intervals, percentile analysis

### Technical Learning Goals
- **Financial Data Engineering**: Extract and structure data from yfinance API
- **Object-Oriented Design**: Build modular, reusable analysis classes
- **Probabilistic Modeling**: Implement Monte Carlo simulation for financial applications
- **Data Visualization**: Create informative plots for distribution analysis

### Real-World Application
This tool enables analysis of current equity markets with:
- Automated data extraction and ratio calculation
- Data-driven parameter estimation (no manual inputs required)
- Probabilistic risk assessment
- Multi-company comparative analysis

---

## Project Architecture

### Core Modules

#### 1. **Data Extraction** (`data_extraction.py`)
**Purpose**: Interface with yfinance API to extract structured financial statement data

**Functionality**:
- Pulls quarterly/annual data from Income Statement, Balance Sheet, Cash Flow Statement
- Structures raw JSON responses into clean Pandas DataFrames
- Handles missing data and API inconsistencies
- Returns time series of 20+ financial metrics per period

**Key Metrics Extracted**:
- **Income Statement**: Revenue, COGS, EBIT, EBITDA, Depreciation, Interest, Net Income
- **Balance Sheet**: Cash, Receivables, Inventory, Assets, Debt, Equity, Retained Earnings
- **Cash Flow**: Operating CF, Capital Expenditures

**Technical Implementation**:
```python
def extract_financial_data(ticker, period='quarterly'):
    # Returns DataFrame: rows = periods, columns = metrics
    # Handles missing data with zero-fill strategy
    # Sorts chronologically for time series analysis
```

---

#### 2. **Ratio Calculation** (`ratios.py`)
**Purpose**: Compute financial ratios for performance analysis

**Implementation**: `RatioCalculator` class operating on single-period data (one row of DataFrame)

**Ratios Implemented**:

**Profitability Metrics**:
- **ROE** (Return on Equity): Net Income / Equity
- **ROA** (Return on Assets): Net Income / Total Assets  
- **Net Margin**: Net Income / Revenue

**Liquidity Metrics**:
- **Current Ratio**: Current Assets / Current Liabilities
- **Quick Ratio**: (Cash + Receivables) / Current Liabilities

**Leverage Metric**:
- **Debt-to-Equity**: Total Debt / Equity

**Cash Flow Metric**:
- **Free Cash Flow (FCF)**: EBIT × (1 - Tax Rate) + Depreciation - CapEx

**Design Pattern**: 
- Single-period calculator (one row in, one set of ratios out)
- Time series function wraps calculator for multi-period analysis
- Handles division by zero gracefully (returns NaN)

---

#### 3. **Deterministic DCF Valuation** (`dcf_analysis.py`)

**Purpose**: Traditional DCF with data-driven parameter estimation

**Methodology**:

1. **Historical Growth Calculation**:
   ```python
   CAGR = (FCF_end / FCF_start)^(1/years) - 1
   ```
   - Uses actual company data to estimate future growth
   - Conservative approach: Use 80% of historical CAGR

2. **WACC Calculation** (Weighted Average Cost of Capital):
   ```
   WACC = (E/V) × r_e + (D/V) × r_d × (1-τ)
   
   Where:
   r_e = Cost of Equity via CAPM: r_f + β × (E[R_m] - r_f)
   r_d = Cost of Debt: Interest Expense / Total Debt
   ```
   
   **Data Sources**:
   - **r_f** (Risk-Free Rate): Current 10-year Treasury yield from yfinance
   - **β** (Beta): Company beta from yfinance market data
   - **E[R_m]** (Market Return): S&P 500 10-year CAGR calculated from historical data
   - **τ** (Tax Rate): Effective tax rate = (EBIT - Interest - Net Income) / (EBIT - Interest)

3. **FCF Projection**:
   - Project 5 years of future FCF using growth rate
   - Year N FCF = Current FCF × (1 + g)^N

4. **Terminal Value** (Perpetuity Growth Model):
   ```
   TV = FCF_terminal × (1 + g_terminal) / (WACC - g_terminal)
   ```
   - Terminal growth typically 2-3% (long-term GDP growth)

5. **Present Value Calculation**:
   ```
   PV = Σ(FCF_t / (1 + WACC)^t) + TV / (1 + WACC)^5
   ```

6. **Equity Value**:
   ```
   Equity Value = Enterprise Value - Net Debt
   Fair Value per Share = Equity Value / Shares Outstanding
   ```

**Key Innovation**: All parameters auto-calculated from data—no manual assumptions required.

---

#### 4. **Monte Carlo DCF Simulation** (`dcf_monte_carlo.py`)

**Purpose**: Probabilistic valuation accounting for parameter uncertainty

**Stochastic Process Design**:

**Parameter Randomization** (Normal Distributions):

1. **Growth Rate**:
   ```
   g_sim ~ N(μ = g_historical, σ = σ_historical)
   ```
   - Mean: Historical CAGR
   - Std Dev: Standard deviation of year-over-year growth rates
   - Bounded: [1%, 30%] to avoid unrealistic extremes

2. **WACC**:
   ```
   WACC_sim ~ N(μ = WACC_base, σ = 0.015)
   ```
   - Mean: Calculated WACC from deterministic model
   - Std Dev: ±1.5% (reflects market volatility)
   - Bounded: [5%, 20%]

3. **Terminal Growth**:
   ```
   g_terminal_sim ~ N(μ = 0.03, σ = 0.005)
   ```
   - Mean: 3% (long-term GDP expectation)
   - Std Dev: ±0.5%
   - Bounded: [1%, 5%]

**Monte Carlo Algorithm**:
```python
for i in range(n_simulations):
    # 1. Draw random parameters
    g = draw_from_normal(μ_growth, σ_growth)
    wacc = draw_from_normal(μ_wacc, σ_wacc)
    g_term = draw_from_normal(μ_terminal, σ_terminal)
    
    # 2. Project FCF with random growth
    fcf_projected = [base_fcf * (1+g)^t for t in 1..5]
    
    # 3. Calculate terminal value
    tv = fcf_5 * (1+g_term) / (wacc - g_term)
    
    # 4. Discount to present value
    pv = sum(fcf_t / (1+wacc)^t) + tv / (1+wacc)^5
    
    # 5. Store fair value
    fair_values[i] = (pv - net_debt) / shares
```

**Output Statistics**:
- **Mean / Median Fair Value**: Central tendency measures
- **Confidence Intervals**: 10th-90th percentile (80% CI), 25th-75th percentile (50% CI)
- **Probability Undervalued**: P(Fair Value > Current Price)
- **Expected Upside**: (Mean FV - Current Price) / Current Price

**Investment Recommendation Logic**:
```python
if P(Undervalued) > 80%  → STRONG BUY
elif P(Undervalued) > 65% → BUY
elif P(Undervalued) > 50% → HOLD
elif P(Undervalued) > 35% → SELL
else                      → STRONG SELL
```

**Why This Approach?**
- **Captures Uncertainty**: Growth and discount rates are not known with certainty
- **Risk Assessment**: Confidence intervals quantify valuation risk
- **Probabilistic Decisions**: Investment decisions based on probability, not single point estimate
- **Realistic**: Acknowledges that all parameters are estimates with error

---

#### 5. **Sensitivity Analysis** (`dcf_sensitivity_analysis.py`)

**Purpose**: Scenario analysis under Bear/Base/Bull cases

**Scenario Definitions**:
- **Bear Case**: 50% of historical growth, conservative terminal growth (2%)
- **Base Case**: 80% of historical growth (realistic), standard terminal growth (3%)
- **Bull Case**: 120% of historical growth, optimistic terminal growth (4%)

**Investment Decision Framework**:
```python
if Bear_upside > 10%  → STRONG BUY (positive even in worst case)
elif Base_upside > 15% → BUY (attractive in realistic case)
elif Bull_upside > 10% → HOLD (only upside in best case)
else                   → AVOID (limited upside across scenarios)
```

**Use Case**: Quick assessment of valuation robustness across assumptions.

---

#### 6. **Comparative Analysis** (`comparative_analysis.py`, `dcf_comparison.py`)

**Purpose**: Multi-company peer analysis and relative valuation

**Ratio Comparison**:
- Side-by-side table of latest financial ratios
- Identify best-in-class performers per metric
- Useful for sector analysis

**DCF Comparison**:
- Runs deterministic DCF for multiple companies
- Ranks by upside potential
- Returns sorted DataFrame: highest upside first

**Monte Carlo Comparison**:
- Runs probabilistic DCF for each company
- Ranks by P(Undervalued)
- Includes confidence intervals and recommendations
- Processing time: ~5-10 seconds per company @ 10k simulations

---

#### 7. **Visualization** (`visualization.py`)

**Plot Types**:

1. **Metric Time Series**: Raw financial statement items over time
   - Revenue, EBIT, Cash trends
   - Absolute performance visualization

2. **Ratio Time Series**: Calculated ratios over time
   - ROE, Debt/Equity trends
   - Relative performance (better than absolute metrics)

3. **Comparative Plots**: Multiple companies on same chart
   - Overlay time series for peer comparison
   - Identify performance divergence

4. **Monte Carlo Distribution Plots** (`plot_monte_carlo_distribution`):
   - **Histogram**: Frequency distribution of fair values with percentile markers
   - **Cumulative Probability**: P(Fair Value < X) curve
   - Includes current price, mean, and confidence interval lines

---

### 8. **Unified Interface** (`MAIN.py`)

**Purpose**: Single-entry-point API for all analysis functions

**Design**: `FinancialAnalysis` class with clean method signatures

**Single-Company Workflow**:
```python
fa = FinancialAnalysis(ticker='AAPL')

# Latest period analysis
ratios = fa.analyze_company(period='quarterly')

# Time series visualization
fa.plot_ratios(['roe', 'debt_to_equity'], period='annual')

# Deterministic DCF (all parameters auto-calculated)
dcf_results = fa.dcf_analysis()

# Scenario analysis
scenarios = fa.dcf_scenarios()

# Monte Carlo DCF (10,000 simulations)
mc_results = fa.mc_dcf_analysis(n_simulations=10000)
fa.plot_monte_carlo_distribution()
```

**Multi-Company Workflow**:
```python
fa = FinancialAnalysis(tickers=['AAPL', 'MSFT', 'GOOGL'])

# Ratio comparison table
comparison = fa.compare_companies(period='annual')

# Time series comparison plots
fa.plot_comparison(['roe', 'net_margin'], period='annual')

# DCF comparison (deterministic)
dcf_comp = fa.dcf_comparison()

# Monte Carlo comparison (probabilistic)
mc_comp = fa.monte_carlo_comparison(n_simulations=10000)
```

---

## Technical Implementation

### Data-Driven Philosophy
**All parameters auto-calculated from historical data—no manual inputs**:
- Growth rates derived from historical CAGR
- WACC calculated from market data (beta, Treasury yields, S&P 500 returns)
- Tax rates extracted from financial statements
- Volatility measured from year-over-year growth variation

This ensures **reproducibility** and **objectivity** in valuation.

### Stochastic Modeling
**Monte Carlo Simulation Features**:
- Normal distributions for parameter uncertainty
- Parameter bounds to avoid unrealistic scenarios
- 10,000+ simulations for statistical stability
- Efficient NumPy vectorization

### Performance Optimization
- **yfinance API**: Single call per company, data cached locally
- **NumPy Operations**: Vectorized calculations (1000x faster than loops)
- **Minimal Dependencies**: Core libraries only (pandas, numpy, matplotlib, yfinance)

### Code Quality
- **Modular Design**: Each module handles single responsibility
- **Type Consistency**: Pandas DataFrames throughout pipeline
- **Error Handling**: Graceful failures with informative messages
- **Documentation**: Docstrings for all public functions

---

## Use Cases & Applications

### 1. **Investment Decision Support**
- **Probabilistic Assessment**: Move beyond "buy/sell" to probability-based decisions
- **Risk Quantification**: Confidence intervals show range of possible outcomes
- **Scenario Planning**: Understand upside in bear/base/bull cases

### 2. **Academic Learning**
- **DCF Mechanics**: Step-by-step implementation of textbook DCF
- **Monte Carlo Methods**: Practical application of stochastic simulation
- **WACC Calculation**: Real implementation of CAPM with live market data
- **Financial Ratios**: Automated calculation from raw statements

### 3. **Sector Analysis**
- **Peer Comparison**: Identify best-performing companies in sector
- **Relative Valuation**: Compare P(Undervalued) across companies
- **Trend Analysis**: Time series plots reveal diverging performance

### 4. **Educational Tool**
- **Transparent Methodology**: All calculations explicit and traceable
- **Data-Driven**: Shows how theory connects to real data
- **Extensible**: Easy to add new ratios, scenarios, or analysis types

---

## Key Results & Insights

### Validation Approach
Tested on major US equities across sectors:
- **Tech**: AAPL, MSFT, GOOGL, NVDA
- **Finance**: JPM, BAC, GS
- **Consumer**: WMT, HD, NKE
- **Healthcare**: JNJ, UNH, PFE

### Findings

#### 1. **Parameter Uncertainty Matters**
- 80% confidence intervals typically span **±30-50%** around mean fair value
- Single-point DCF masks substantial uncertainty
- P(Undervalued) more informative than point estimate upside

#### 2. **Historical Growth Predictive but Volatile**
- Historical CAGR reasonable baseline for projections
- Growth volatility varies significantly across companies:
  - **Stable**: Consumer staples (σ ~ 5-10%)
  - **Volatile**: Tech hardware (σ ~ 15-25%)
- Volatility should influence position sizing

#### 3. **Data-Driven WACC Aligns with Theory**
- Calculated WACC typically 8-12% for large-cap US equities
- Beta correlation with sector risk intuitive (Tech > Finance > Consumer Staples)
- Effective tax rates often differ from statutory (21%)—data-driven approach captures this

#### 4. **Monte Carlo Recommendations More Robust**
- Deterministic DCF can give false precision
- Probabilistic framework forces acknowledgment of uncertainty
- Investment decisions more defensible when probability-based

---

## Technical Skills Demonstrated

### Financial Theory & Valuation
- **DCF Methodology**: Free Cash Flow projection, terminal value, discounting
- **WACC Calculation**: CAPM, cost of equity/debt, capital structure weighting
- **Ratio Analysis**: Profitability, liquidity, leverage metrics
- **Effective Tax Rate Calculation**: From financial statements

### Stochastic Modeling
- **Monte Carlo Simulation**: Parameter randomization, distribution sampling
- **Probability Distributions**: Normal distributions for continuous variables
- **Statistical Inference**: Confidence intervals, percentiles, probability assessment
- **Volatility Measurement**: Historical standard deviation of growth rates

### Software Engineering
- **Object-Oriented Design**: Modular classes with single responsibilities
- **API Integration**: yfinance data extraction and error handling
- **Data Structures**: Pandas DataFrames for time series financial data
- **Code Organization**: Separation of concerns across 8+ modules

### Data Science & Visualization
- **Data Cleaning**: Handling missing values, API inconsistencies
- **Time Series Analysis**: Historical trend calculation, CAGR computation
- **Statistical Visualization**: Distribution histograms, cumulative probability plots
- **Comparative Analysis**: Multi-company time series plots

### Numerical Computing
- **NumPy Vectorization**: Efficient array operations for 10k+ simulations
- **Mathematical Operations**: CAGR, NPV, weighted averages
- **Percentile Calculations**: Confidence interval bounds

---

## Dependencies

```
yfinance>=0.2.0        # Financial data API
pandas>=2.0.0          # Data structures and analysis
numpy>=1.24.0          # Numerical computing
matplotlib>=3.7.0      # Plotting and visualization
```

Install:
```bash
pip install -r requirements.txt
```

---

## Usage Examples

### Quick Start: Single Company Analysis
```python
from MAIN import FinancialAnalysis

# Initialize
fa = FinancialAnalysis(ticker='AAPL')

# Latest ratios
ratios = fa.analyze_company(period='quarterly')
print(ratios)

# Historical trends
fa.plot_ratios(['roe', 'roa', 'net_margin'], period='annual')

# Deterministic DCF
dcf = fa.dcf_analysis()
print(f"Fair Value: ${dcf['fair_value']:.2f}")
print(f"Upside: {dcf['upside_pct']:.1f}%")

# Monte Carlo DCF
mc = fa.mc_dcf_analysis(n_simulations=10000)
print(f"P(Undervalued): {mc['prob_undervalued']:.1f}%")
print(f"Recommendation: {mc['recommendation']}")

# Visualize distribution
fa.plot_monte_carlo_distribution()
```

### Multi-Company Comparison
```python
fa = FinancialAnalysis(tickers=['AAPL', 'MSFT', 'GOOGL'])

# Ratio comparison
comparison = fa.compare_companies(period='annual')
print(comparison)

# Plot comparison
fa.plot_comparison(['roe', 'net_margin'], period='annual')

# Monte Carlo comparison
mc_comp = fa.monte_carlo_comparison(n_simulations=10000)
print(mc_comp.sort_values('P(Undervalued) %', ascending=False))
```

### Custom DCF with Manual Parameters
```python
fa = FinancialAnalysis(ticker='AAPL')

# Override default parameters
dcf = fa.dcf_analysis(
    growth_rate=0.10,        # 10% growth
    terminal_growth=0.025,   # 2.5% terminal
    risk_free_rate=0.04,     # 4% risk-free
    tax_rate=0.21,           # 21% tax
    years=7                  # 7-year projection
)
```

---

## Limitations & Future Enhancements

### Current Limitations
1. **US Equities Only**: yfinance API optimized for US markets
2. **FCF-Based Valuation**: Not suitable for high-growth companies with negative FCF
3. **No Sector Adjustments**: WACC calculation doesn't adjust for sector-specific risks
4. **API Dependency**: Requires yfinance availability (occasional downtime)

### Potential Enhancements
1. **Relative Valuation**: Add P/E, EV/EBITDA multiples analysis
2. **Sector Benchmarking**: Compare metrics against sector averages
3. **Historical Backtesting**: Test DCF predictions against realized returns
4. **Correlation Analysis**: Model correlated uncertainties (e.g., growth and margins)
5. **Advanced Monte Carlo**: Latin Hypercube Sampling for better coverage
6. **Machine Learning**: Predict growth rates using ML on fundamentals
7. **Multi-Asset Class**: Extend to bonds, currencies, commodities

---

## Learning Outcomes

This project demonstrates:
- **Financial Theory Application**: Translating textbook DCF into working code
- **Stochastic Methods**: Practical Monte Carlo simulation for uncertainty quantification
- **Data Engineering**: Extracting and structuring financial data from APIs
- **Software Design**: Building modular, extensible analysis framework
- **Probabilistic Thinking**: Moving from point estimates to probability distributions

---

## Author

**Matteo Fantuz**  
B.Sc. Economics and Finance, University of Bologna (Expected 2026)  
Exchange Student, University of British Columbia (Fall 2025)

**Context**: Developed as extension of Corporate Finance coursework, applying valuation theory to real market data with stochastic modeling.

**Contact**: matteofantuz04@gmail.com  
**GitHub**: [github.com/fan-tuz](https://github.com/fan-tuz)