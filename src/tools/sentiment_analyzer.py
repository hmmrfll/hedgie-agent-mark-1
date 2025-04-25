# src/tools/sentiment_analyzer.py

from typing import List, Dict, Any
import logging
from transformers import pipeline

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Инструмент для анализа тональности текста с использованием BERT"""
    
    def __init__(self):
        try:
            # Загружаем предобученную модель BERT для анализа тональности
            self.sentiment_pipeline = pipeline("sentiment-analysis", model="finiteautomata/bertweet-base-sentiment-analysis")
            logger.info("Модель BERT успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели BERT: {e}")
            self.sentiment_pipeline = None

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Анализ тональности текста"""
        if not self.sentiment_pipeline:
            return {"label": "NEUTRAL", "score": 0.5}
            
        try:
            result = self.sentiment_pipeline(text)[0]
            return result
        except Exception as e:
            logger.error(f"Ошибка при анализе тональности: {e}")
            return {"label": "NEUTRAL", "score": 0.5}

    def analyze_news(self, articles: List[Dict], currency: str) -> Dict[str, Any]:
        """Анализ тональности новостей"""
        if not articles:
            return {'sentiment_analysis': 'no_data'}

        sentiments = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        # Анализируем заголовки новостей
        for article in articles:
            title = article.get('title', '')
            if not title:
                continue
                
            sentiment = self.analyze_text(title)
            label = sentiment.get('label', 'NEUTRAL')
            score = sentiment.get('score', 0.5)
            
            # Собираем результаты
            sentiments.append({
                'title': title,
                'label': label,
                'score': score
            })
            
            # Подсчитываем количество по тональности
            if label == 'POSITIVE':
                positive_count += 1
            elif label == 'NEGATIVE':
                negative_count += 1
            else:
                neutral_count += 1

        # Анализируем соотношение положительных/отрицательных новостей
        total = len(sentiments)
        positive_ratio = positive_count / total if total > 0 else 0
        negative_ratio = negative_count / total if total > 0 else 0
        
        # Определяем общую тональность
        overall_sentiment = "neutral"
        if positive_ratio > 0.6:
            overall_sentiment = "strongly positive"
        elif positive_ratio > 0.4:
            overall_sentiment = "positive"
        elif negative_ratio > 0.6:
            overall_sentiment = "strongly negative"
        elif negative_ratio > 0.4:
            overall_sentiment = "negative"
            
        return {
            'sentiment_analysis': {
                'total_analyzed': total,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'positive_ratio': positive_ratio,
                'negative_ratio': negative_ratio,
                'overall_sentiment': overall_sentiment,
                'sentiments': sentiments[:10]  # Возвращаем первые 10 результатов
            }
        }