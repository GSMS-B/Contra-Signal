import google.generativeai as genai
import json
import logging
from backend.config import GEMINI_API_KEY
from backend.models.schemas import ContrarianSignal, NewsSentiment, FundamentalMetrics, PeerComparison
from backend.utils.ai_helper import generate_content_with_retry

logger = logging.getLogger(__name__)
genai.configure(api_key=GEMINI_API_KEY)

class SignalGenerator:
    def generate_signal(self, news: NewsSentiment, fundamentals: FundamentalMetrics, peers: PeerComparison) -> ContrarianSignal:
        
        prompt = f"""
        Act as a contrarian investment analyst (Warren Buffett style).
        Identify if there is a panic selling opportunity (Buying good company on bad news).

        News Analysis: {news.model_dump_json()}
        Fundamentals: {fundamentals.model_dump_json()}
        Peer Comparison: {peers.model_dump_json()}

        Rules:
        - Strong Buy: Negative Sentiment + Strong Fundamentals + Leader Peers
        - Buy: Mixed/Neg Sentiment + Good Fundamentals
        - Avoid: Bad Fundamentals (regardless of news)
        - Hold: Mixed signals

        Return JSON object (no markdown):
        {{
            "signal_type": "<Strong Buy|Buy|Hold|Avoid>",
            "signal_strength": <int, 0-10>,
            "confidence": "<High|Medium|Low>",
            "summary": "1-2 sentence summary",
            "opportunity_reasons": ["reason1", "reason2"],
            "risk_factors": ["risk1", "risk2"],
            "management_outlook": "Summarize key managerial decisions or strategic pivots mentioned in reports",
            "future_development": "Summarize future growth plans, R&D, or expansion goals",
            "timeframe": "e.g. 3-6 months",
            "entry_strategy": "e.g. Staggered buying"
        }}
        """

        try:
            print(f"\n[Signal Generator] Synthesizing final signal...")
            model_flash = genai.GenerativeModel('models/gemma-3-27b-it')
            response = generate_content_with_retry(model_flash, prompt)
            print(f"[Signal Generator] Gemini Final Decision:\n{response.text}")
            data = json.loads(response.text.replace("```json", "").replace("```", ""))
            return ContrarianSignal(**data)
        except Exception as e:
            print(f"!!! [Signal Generator] ERROR: {e}")
            logger.error(f"Signal Gen failed: {e}")
            return ContrarianSignal(
                signal_type="Hold", signal_strength=5, confidence="Low",
                summary=f"Analysis failed: {str(e)}", opportunity_reasons=[], risk_factors=[],
                management_outlook="Unknown", future_development="Unknown",
                timeframe="Unknown", entry_strategy="Wait"
            )
