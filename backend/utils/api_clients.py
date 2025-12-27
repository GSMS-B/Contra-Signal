import requests
import logging
from typing import List, Dict
import time
from backend.config import NEWS_API_KEY

logger = logging.getLogger(__name__)

class NewsAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"

    def fetch_news(self, company_name: str, days: int = 7) -> List[Dict]:
        """
        Fetches news for the given company from the last `days`.
        """
        try:
            response = requests.get(
                self.base_url,
                params={
                    'q': company_name,
                    'apiKey': self.api_key,
                    'language': 'en',
                    'sortBy': 'publishedAt', # Ensure latest news comes first
                    'pageSize': 20
                }
            )
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            # Normalize format
            clean_articles = []
            for art in articles:
                clean_articles.append({
                    'title': art.get('title'),
                    'description': art.get('description'),
                    'url': art.get('url'),
                    'published_at': art.get('publishedAt'),
                    'source': art.get('source', {}).get('name')
                })
            return clean_articles

        except Exception as e:
            print(f"!!! [NewsAPI] ERROR: {e}")
            logger.error(f"NewsAPI error: {str(e)}")
            return []

class NewsAggregator:
    def __init__(self):
        self.client = NewsAPIClient(api_key=NEWS_API_KEY)

    def fetch_news(self, company_name: str) -> List[Dict]:
        # In a full production app, this would try multiple clients
        return self.client.fetch_news(company_name)
