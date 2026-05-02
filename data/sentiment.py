# data/sentiment.py — News headline sentiment via NewsAPI + FinBERT

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

def get_sentiment_score(keyword="Bitcoin"):
    """
    Returns a float: positive > 0.5 = bullish, < 0.5 = bearish.
    Returns 0.5 (neutral) if sentiment is disabled or fails.
    """
    if not config.SENTIMENT_ENABLED:
        return 0.5  # neutral

    try:
        import requests
        from transformers import pipeline

        url = (
            f"https://newsapi.org/v2/everything?q={keyword}"
            f"&sortBy=publishedAt&pageSize=10&apiKey={config.NEWSAPI_KEY}"
        )
        articles = requests.get(url, timeout=10).json().get('articles', [])
        headlines = [a['title'] for a in articles if a.get('title')]

        if not headlines:
            return 0.5

        # FinBERT — financial sentiment model
        nlp = pipeline("sentiment-analysis",
                       model="ProsusAI/finbert",
                       truncation=True, max_length=512)
        results = nlp(headlines[:5])

        score = 0.0
        for r in results:
            if r['label'] == 'positive':
                score += r['score']
            elif r['label'] == 'negative':
                score -= r['score']

        # Normalise to 0-1 range
        normalised = (score / len(results) + 1) / 2
        return round(max(0.0, min(1.0, normalised)), 4)

    except Exception as e:
        print(f"[Sentiment] Error: {e}")
        return 0.5
