import google.generativeai as genai
import json
import os
import logging
from backend.config import GEMINI_API_KEY
from backend.models.schemas import PeerComparison, FundamentalMetrics
from backend.utils.ai_helper import generate_content_with_retry

logger = logging.getLogger(__name__)
genai.configure(api_key=GEMINI_API_KEY)

class PeerComparator:
    def __init__(self):
        # Load peer groups
        try:
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'peer_groups.json')
            with open(path, 'r') as f:
                self.peer_groups = json.load(f)
        except Exception:
            self.peer_groups = {}

    def get_peers(self, company_name: str):
        # Simple lookup
        for key, peers in self.peer_groups.items():
            if key.lower() in company_name.lower():
                return peers
        return []

    def analyze(self, company_name: str, target_metrics: FundamentalMetrics) -> PeerComparison:
        peers = self.get_peers(company_name)
        print(f"\n[Peer Comparator] Comparing {company_name} with: {peers}")
        
        # MOCKED PEER DATA FOR HACKATHON
        # In real app, we would fetch/analyze peer reports
        peer_metrics_map = {}
        for p in peers:
            # Generate plausible variance from target
            peer_metrics_map[p] = FundamentalMetrics(
                revenue_growth=target_metrics.revenue_growth * 0.9, 
                profit_margin=target_metrics.profit_margin * 0.95,
                roe=target_metrics.roe * 0.9,
                debt_to_equity=target_metrics.debt_to_equity * 1.1,
                health_score=max(0, target_metrics.health_score - 1),
                strengths=[], concerns=[]
            )

        prompt = f"""
        Compare {company_name} with its peers: {', '.join(peers)}.
        
        Target Metrics: {target_metrics.model_dump_json()}
        Peer Metrics (simulated): {json.dumps({k: v.model_dump() for k, v in peer_metrics_map.items()})}

        Return JSON:
        {{
            "competitive_position": "<leader|average|laggard>",
            "relative_strength": <int, 0-10>,
            "summary": "Brief comparison summary"
        }}
        """

        try:
            print(f"[Peer Comparator] Sending comparison prompt...")
            model_flash = genai.GenerativeModel('models/gemma-3-27b-it')
            response = generate_content_with_retry(model_flash, prompt)
            print(f"[Peer Comparator] Gemini Response:\n{response.text}")
            data = json.loads(response.text.replace("```json", "").replace("```", ""))
            
            return PeerComparison(
                competitive_position=data['competitive_position'],
                relative_strength=data['relative_strength'],
                peer_metrics=peer_metrics_map
            )
        except Exception as e:
            print(f"!!! [Peer Comparator] ERROR: {e}")
            logger.error(f"Peer Compare failed: {e}")
            return PeerComparison(
                competitive_position="average", relative_strength=5, peer_metrics={}
            )
