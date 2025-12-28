import pandas as pd
from typing import Dict, Any

def safe_float(val):
    if val is None or val == '':
        return 0.0
    try:
        return float(val)
    except:
        return 0.0

def normalize_linear(value: float, min_val: float, max_val: float) -> float:
    """
    Linear normalization to 0-100 scale
    """
    if value is None or pd.isna(value):
        return 50.0  # Neutral if missing
    
    if value <= min_val:
        return 0.0
    elif value >= max_val:
        return 100.0
    else:
        return ((value - min_val) / (max_val - min_val)) * 100.0

def calculate_normalized_scores_v2(raw_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Enhanced normalization with Dividend Yield
    """
    
    # 1. GROWTH (5Y Returns)
    # Scale: -20% = 0, 0% = 40, 100% = 100
    returns_5y = raw_data.get('returns_5y')
    if returns_5y is not None:
        growth_score = normalize_linear(returns_5y, min_val=-20, max_val=100)
    else:
        growth_score = 50.0
    
    # 2. PROFITABILITY (ROE)
    # Scale: 0% = 0, 15% = 50, 30%+ = 100
    roe = raw_data.get('roe')
    if roe is not None:
        profitability_score = normalize_linear(roe, min_val=0, max_val=30)
    else:
        profitability_score = 50.0
    
    # 3. EFFICIENCY (ROCE)
    # Scale: 0% = 0, 15% = 50, 30%+ = 100
    roce = raw_data.get('roce')
    if roce is not None:
        efficiency_score = normalize_linear(roce, min_val=0, max_val=30)
    else:
        efficiency_score = 50.0
    
    # 4. VALUATION (P/E vs Industry P/E)
    # Closer to industry P/E = better
    pe_ratio = raw_data.get('pe_ratio')
    industry_pe = raw_data.get('industry_pe')
    
    if pe_ratio and industry_pe and industry_pe > 0:
        # Calculate deviation percentage
        deviation = abs(pe_ratio - industry_pe) / industry_pe * 100
        
        # 0% deviation = 100 score
        # 50%+ deviation = 0 score
        valuation_score = max(0, 100 - (deviation * 2))
        
        # Bonus: Slight preference for undervalued (P/E < Industry)
        if pe_ratio < industry_pe:
            valuation_score = min(100, valuation_score * 1.1)
    else:
        # If P/E is valid but industry PE is missing, maybe assume fair?
        # Or if PE is 0 (loss making), low score?
        if pe_ratio and pe_ratio < 0: valuation_score = 20 # Loss making
        else: valuation_score = 50.0
    
    # 5. DIVIDEND YIELD (NEW)
    # Use pre-calculated yield if present, else calculate
    dividend_yield = raw_data.get('dividend_yield')
    if dividend_yield is None:
        dividend = raw_data.get('dividend', 0.0)
        current_price = raw_data.get('current_price', 0.0)
        
        if dividend and current_price and current_price > 0:
            dividend_yield = (dividend / current_price) * 100
        else:
            dividend_yield = 0.0
            
    # Scale: 0% = 0, 2% = 50, 5%+ = 100
    dividend_score = normalize_linear(dividend_yield, min_val=0, max_val=5)
    
    # 6. MOMENTUM (1Y Returns)
    # Scale: -50% = 0, 0% = 50, 100% = 100
    returns_1y = raw_data.get('returns_1y')
    if returns_1y is not None:
        momentum_score = normalize_linear(returns_1y, min_val=-50, max_val=100)
    else:
        momentum_score = 50.0
    
    return {
        "Growth": round(growth_score, 1),
        "Profitability": round(profitability_score, 1),
        "Efficiency": round(efficiency_score, 1),
        "Valuation": round(valuation_score, 1),
        "Dividend Yield": round(dividend_score, 1),
        "Momentum": round(momentum_score, 1)
    }
