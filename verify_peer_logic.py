from backend.utils.peer_comparison import calculate_normalized_scores_v2
import json

def test_normalization():
    print("Testing Normalization Logic...")
    
    # Case 1: High Growth, High Profit
    sample_1 = {
        'returns_5y': 150.0, # Expect 100
        'roe': 35.0,         # Expect 100
        'roce': 40.0,        # Expect 100
        'pe_ratio': 20.0,
        'industry_pe': 25.0, # Undervalued -> Expect high score
        'dividend_yield': 1.5, # Expect ~37.5 (1.5/4 * 100 ?) No, range 0-5. 1.5/5 * 100 = 30? Wait formula is linear 0-5.
        'returns_1y': 80.0   # Expect High
    }
    
    scores_1 = calculate_normalized_scores_v2(sample_1)
    print(f"\nSample 1 (High Performance):\n{json.dumps(scores_1, indent=2)}")
    
    # Case 2: Poor Performance
    sample_2 = {
        'returns_5y': -30.0, # Expect 0 (min -20)
        'roe': -5.0,         # Expect 0
        'roce': 2.0,         # Expect low
        'pe_ratio': 50.0,
        'industry_pe': 25.0, # Overvalued -> Expect low score
        'dividend_yield': 0.0, # Expect 0
        'returns_1y': -60.0  # Expect 0 (min -50)
    }
    
    scores_2 = calculate_normalized_scores_v2(sample_2)
    print(f"\nSample 2 (Poor Performance):\n{json.dumps(scores_2, indent=2)}")
    
    # Case 3: Average / Missing
    sample_3 = {
        'pe_ratio': 25.0,
        'industry_pe': 25.0 # Fair value
        # Others missing -> Expect 50
    }
    
    scores_3 = calculate_normalized_scores_v2(sample_3)
    print(f"\nSample 3 (Average/Missing):\n{json.dumps(scores_3, indent=2)}")

if __name__ == "__main__":
    try:
        test_normalization()
        print("\n✅ Verification Successful: Logic runs without errors.")
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
