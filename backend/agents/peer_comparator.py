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
        # We no longer rely on static peer groups JSON
        pass

    from typing import List
    def analyze(self, company_name: str, target_metrics: FundamentalMetrics, manual_competitors: List[str] = []) -> PeerComparison:
        from backend.utils.ticker_db import get_ticker_db
        db = get_ticker_db()
        
        peer_data_list = []
        peer_names = []
        
        # 1. Handle Manual Competitors (High Priority)
        # We process them in order they came
        for mc_name in manual_competitors:
             if len(peer_data_list) >= 5:
                 break # Max 4 peers
             
             print(f"[Peer Comparator] Fetching manual competitor: {mc_name}")
             comp_data = db.get_company_details(mc_name)
             if comp_data:
                 comp_data['Name'] = mc_name 
                 peer_data_list.append(comp_data)
             else:
                 print(f"[Peer Comparator] Manual competitor '{mc_name}' not found.")

        # 2. Identify Automated Peers using Industry PE (Fill remaining slots)
        needed = 5 - len(peer_data_list)
        if needed > 0:
            print(f"\n[Peer Comparator] Finding additional peers for {company_name} (Ind. PE: {target_metrics.industry_pe})...")
            auto_peers = db.get_peers_by_industry(
                industry_pe=target_metrics.industry_pe,
                exclude_name=company_name,
                limit=needed * 2  # Fetch extra to filter
            )
            
            # Filter out already added manual competitors
            current_names = [p.get('Name') for p in peer_data_list]
            
            for p in auto_peers:
                if len(peer_data_list) >= 5: break
                p_name = p.get('Name')
                if p_name in current_names: continue
                if p_name in manual_competitors: continue # extra safe
                
                peer_data_list.append(p)
        
        peer_metrics_map = {}

        # 3. Populate Metrics for Peers from CSV
        for p_data in peer_data_list:
            p_name = p_data.get('Name')
            peer_names.append(p_name)
            
            # Convert CSV dict to FundamentalMetrics object
            # Note: We only fill quantitative, qualitative will be defaults
            p_metrics = FundamentalMetrics(
                market_cap=p_data.get('Market Cap (Cr.)', 0.0),
                pe_ratio=p_data.get('PE Ratio', 0.0),
                industry_pe=p_data.get('Industry PE', 0.0),
                roe=p_data.get('ROE', 0.0),
                roce=p_data.get('ROCE', 0.0),
                eps=p_data.get('EPS', 0.0),
                pb_ratio=p_data.get('PB Ratio', 0.0),
                dividend_yield=p_data.get('Dividend', 0.0),
                
                returns_1y=p_data.get('1 Yr Returns', 0.0),
                # Add other returns if needed for comparison view
                
                health_score=5, # Default since we don't analyze peers deeply
                strengths=[],
                concerns=[]
            )
            peer_metrics_map[p_name] = p_metrics

        print(f"[Peer Comparator] Found peers: {peer_names}")

        # 4. Generate Comparative Narrative
        prompt = f"""
        Compare {company_name} with these industry peers: {', '.join(peer_names)}.
        
        Target Stock ({company_name}) Metrics:
        PE: {target_metrics.pe_ratio}, Industry PE: {target_metrics.industry_pe}, ROE: {target_metrics.roe}, ROCE: {target_metrics.roce}, 1Y Return: {target_metrics.returns_1y}%
        
        Peer Metrics:
        {json.dumps({k: {'PE': v.pe_ratio, 'ROE': v.roe, 'MarketCap': v.market_cap} for k, v in peer_metrics_map.items()})}

        Task:
        1. Determine if {company_name} is overvalued or undervalued compared to peers.
        2. Is it a "leader", "average", or "laggard"?
        3. Assign a Relative Strength score (0-10) where 10 means it dominates peers.
        
        Return JSON:
        {{
            "competitive_position": "<leader|average|laggard>",
            "relative_strength": <int, 0-10>
        }}
        """

        try:
            print(f"[Peer Comparator] Sending comparison prompt...")
            model_flash = genai.GenerativeModel('models/gemma-3-27b-it')
            response = generate_content_with_retry(model_flash, prompt)
            data = json.loads(response.text.replace("```json", "").replace("```", ""))
            
            return PeerComparison(
                competitive_position=data.get('competitive_position', 'average'),
                relative_strength=data.get('relative_strength', 5),
                peer_metrics=peer_metrics_map
            )
        except Exception as e:
            print(f"!!! [Peer Comparator] ERROR: {e}")
            logger.error(f"Peer Compare failed: {e}")
            return PeerComparison(
                competitive_position="average", relative_strength=5, peer_metrics=peer_metrics_map
            )
