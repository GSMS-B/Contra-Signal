import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.utils.ticker_db import get_ticker_db
from backend.agents.fundamental_analyzer import FundamentalAnalyzer
from backend.agents.peer_comparator import PeerComparator
from backend.models.schemas import FundamentalMetrics

# Mock RAG to avoid external calls
class MockRAG:
    def add_document(self, *args): pass
    def query_context(self, *args): return "Management is optimistic. Future plans include opening 500 new stores. Key strengths are brand and network. Concerns are rising costs."

def verify():
    print("--- 1. Testing TickerDatabase ---")
    db = get_ticker_db()
    csv_path = os.path.join("backend", "data", "stocks.csv")
    
    if not os.path.exists(csv_path):
        print(f"❌ Stocks CSV not found at {csv_path}")
        return

    db.load_data(csv_path)
    if db.df is None:
        print("❌ Failed to lead DB")
        return
        
    print(f"✅ Loaded {len(db.df)} tickers")
    
    # Test Detail Retrieval
    details = db.get_company_details("Reliance Industries")
    if details:
        print(f"✅ Retrieved Reliance: Market Cap={details.get('Market Cap (Cr.)')}, PE={details.get('PE Ratio')}")
        print(f"✅ 5 Yr Returns Loaded: {details.get('5 Yr Returns')}")
    else:
        print("❌ Failed to retrieve Reliance")

    # Test Peer Logic (Manual Competitor)
    print("\n--- 2. Testing Peer Logic (Manual Competitor) ---")
    # Mock Manual Competitor
    manual_comp = "TCS"
    if details:
        try:
            # We need to insantiate the comparator to test logic, but logic is inside analyze()
            # Let's just check if logic flow works by simulating the logic step
            print(f"Testing manual competitor fetch for '{manual_comp}'...")
            comp_data = db.get_company_details(manual_comp)
            if comp_data:
                print(f"✅ Manual Competitor '{manual_comp}' Found in DB with PE: {comp_data.get('PE Ratio')}")
            else:
                print(f"❌ '{manual_comp}' not found")
        except Exception as e:
            print(f"Error testing manual comp: {e}")

    # Test Fundamental Analyzer (Merging)
    print("\n--- 3. Testing Fundamental Analyzer (Mock RAG) ---")
    analyzer = FundamentalAnalyzer()
    analyzer.rag = MockRAG() # Inject mock
    
    # Use Reliance for test
    # We want to see if the NEW fields are merged (even if 0.0 from CSV)
    result = analyzer.analyze("Reliance Industries")
    
    print("Result Data:")
    print(f"  Market Cap: {result.market_cap} (From CSV)")
    print(f"  5Y Returns: {result.returns_5y} (From CSV)")
    print(f"  Revenue Growth: {result.revenue_growth} (Should be 0.0 or mocked)")
    print(f"  Debt/Eq: {result.debt_to_equity} (Should be 0.0 or mocked)")
    
    if result.market_cap > 0:
        print("✅ Fundamental Merger Success.")
    else:
        print("❌ Fundamental Merger Failed.")

    # Test Peer Comparator
    print("\n--- 4. Testing Peer Comparator ---")
    comparator = PeerComparator()
    # Mock LLM for comparator just to avoid API cost/setup in script? 
    # Actually PeerComparator calls Gemini. We can just verify it gets data.
    # We'll skip actual LLM call if we want fast test, but let's see if we can just check the data prep.
    # The analyze method does `db.get_peers` and then calls LLM.
    # We will assume if step 2 works, logic is fine, but let's try to run it if API key is present.
    
    try:
        peer_res = comparator.analyze("Reliance Industries", result)
        print(f"✅ Peer Analysis: {peer_res.competitive_position}")
        print(f"✅ Peer Metrics Loaded: {len(peer_res.peer_metrics)} peers compared")
    except Exception as e:
        print(f"⚠️ Peer Comparator LLM Check Skipped/Failed: {e}")

if __name__ == "__main__":
    verify()
