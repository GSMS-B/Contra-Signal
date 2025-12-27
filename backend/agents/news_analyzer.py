import google.generativeai as genai
import json
import logging
from typing import Dict, List
from backend.config import GEMINI_API_KEY
from backend.utils.api_clients import NewsAggregator
from backend.models.schemas import NewsSentiment
from backend.utils.ai_helper import generate_content_with_retry

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

class NewsAnalyzer:
    def __init__(self):
        self.aggregator = NewsAggregator()

    def analyze(self, company_name: str) -> NewsSentiment:
        # 1. Fetch News
        articles = self.aggregator.fetch_news(company_name)
        
        if not articles:
            # Return neutral fallback if no news
            return NewsSentiment(
                score=0, positive_count=0, negative_count=0, neutral_count=0,
                key_themes=["No recent news found"], headlines=[], panic_level="low"
            )

        # 2. Prepare Prompt
        print(f"\n[News Analyzer] Fetched {len(articles)} articles. Top headlines:")
        for a in articles[:3]:
            print(f" - {a['title']}")

        articles_text = "\n".join([f"- {a['title']} ({a['source']}): {a['description']}" for a in articles[:15]])
        
        prompt = f"""
        Analyze the news sentiment for {company_name}.
        
        Articles:
        {articles_text}
        
        Return a JSON object with this EXACT structure (no markdown):
        {{
            "score": <int, -10 to 10>,
            "positive_count": <int>,
            "negative_count": <int>,
            "neutral_count": <int>,
            "key_themes": [<list of strings>],
            "headlines": [<list of top 5 headlines as strings>],
            "panic_level": "<low|medium|high>"
        }}
        """

        # 3. Call Gemini
        try:
            print("[News Analyzer] Sending prompt to Gemini...")
            
            # Print top 5 headlines for debugging as requested
            print("\n[DEBUG] Top 5 Headlines Sent to AI:")
            print(articles_text.split('\n')[:5])
            
            model_flash = genai.GenerativeModel('models/gemma-3-27b-it')
            response = generate_content_with_retry(model_flash, prompt)
            print(f"[News Analyzer] Gemini Response:\n{response.text}")
            text = response.text.strip()
            # Clean markdown if present
            if text.startswith("```json"):
                text = text[7:-3]
            
            data = json.loads(text)
            return NewsSentiment(**data)
        except Exception as e:
            print(f"!!! [News Analyzer] ERROR: {e}")
            logger.error(f"News Analysis failed: {e}")
            return NewsSentiment(
                score=0, positive_count=0, negative_count=0, neutral_count=0,
                key_themes=[f"Error: {str(e)}"], headlines=[], panic_level="low"
            )
