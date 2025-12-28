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

        # Prepare all headlines for the UI (not just 15, but maybe limit to 20 for prompt token safety if needed, but return ALL to UI)
        # Actually logic: We pass top 20 to LLM, but we can return ALL titles in the 'headlines' field for the UI list
        all_headlines = [a['title'] for a in articles]
        
        articles_text = "\n".join([f"- {a['title']} ({a['source']}): {a['description']}" for a in articles[:25]])
        
        prompt = f"""
        Analyze the news sentiment for {company_name}.
        
        CRITICAL FILTERING: 
        - IGNORE news about "Sector", "Sensex", "Nifty", or other companies unless {company_name} is explicitly involved.
        - Focus ONLY on {company_name}.
        
        Articles:
        {articles_text}
        
        Tasks:
        1. Calculate Sentiment Score (-10 to 10).
        2. RATE SEVERITY (0-10): How critical is this news to the company's survival/integrity?
           - 10: Fraud, Raid, Liquidation, Bankruptcy, CEO Arrest. (KILL SWITCH)
           - 7-9: Major Regulatory Fine, Factory Fire, Massive Strike.
           - 4-6: Bad Earnings, Product Recall.
           - 0-3: Routine news, market noise.
        
        Return JSON object (no markdown):
        {{
            "score": <int, -10 to 10>,
            "positive_count": <int>,
            "negative_count": <int>,
            "neutral_count": <int>,
            "key_themes": [<list of strings>],
            "headlines": [{{ "title": "Example Headline", "sentiment": "positive" }}],  # Return ALL analyzed headlines with sentiment labels (positive/negative/neutral)
            "panic_level": "<low|medium|high>",
            "severity_score": <int, 0-10>,
            "severity_reason": "<short explanation>"
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
            
            # --- Override headlines logic no longer needed, we want LLM to tag them ---
            # However, if LLM only returns top few, we might miss some. 
            # Ideally, we want LLM to tag ALL provided articles.
            # For robustness, we will trust the LLM's returned list if it matches roughly the input count.
            # If empty, we fallback.
            
            if not data.get('headlines'):
                 data['headlines'] = [{"title": t, "sentiment": "neutral"} for t in all_headlines]
            
            # Sort headlines: Prioritize Positive/Negative over Neutral
            if data.get('headlines'):
                def sentiment_priority(h):
                    s = (h.get('sentiment') or 'neutral').lower()
                    if s == 'positive': return 0
                    if s == 'negative': return 1
                    return 2 # Neutral last
                
                data['headlines'].sort(key=sentiment_priority)

            return NewsSentiment(**data)
        except Exception as e:
            print(f"!!! [News Analyzer] ERROR: {e}")
            logger.error(f"News Analysis failed: {e}")
            return NewsSentiment(
                score=0, positive_count=0, negative_count=0, neutral_count=0,
                key_themes=[f"Error: {str(e)}"], headlines=[], panic_level="low"
            )
