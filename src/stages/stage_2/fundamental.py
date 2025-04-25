# src/stages/stage_2/fundamental.py

from typing import Dict, List, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FundamentalAnalyzer:
    """Анализатор фундаментальных факторов"""
    
    def __init__(self, tools, memory, communicator):
        self.tools = tools
        self.memory = memory
        self.communicator = communicator

    def analyze(self, currency: str, days: int) -> Dict[str, Any]:
        """Выполнение фундаментального анализа"""
        self.communicator.say("\nНачинаю фундаментальный анализ...")
        
        # Получение новостей
        news_data = self._collect_news(currency, days)
        
        # Анализ новостей
        news_analysis = self._analyze_news(news_data)
        
        # Подготовка результатов
        results = self._prepare_results(news_analysis)
        
        return results

    def _collect_news(self, currency: str, days: int) -> Dict[str, Any]:
        """Сбор новостей"""
        self.communicator.say("Получаю новости...")
        news = self.tools.get_news(currency, days)
        
        if news['status'] == 'success':
            self.communicator.say(f"Найдено {news['total_results']} новостей")
        else:
            self.communicator.show_warning("Проблемы при получении новостей")
            
        return news

    def _analyze_news(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ новостей"""
        if news_data['status'] != 'success':
            return {'status': 'error', 'message': 'Нет данных для анализа'}

        self.communicator.say("Анализирую новостной фон...")
        currency = news_data.get('currency', 'BTC')  # получаем валюту из новостных данных
        return self.tools.analyze_news(news_data['articles'], currency)

    def _prepare_results(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовка результатов анализа"""
        if analysis.get('status') == 'error':
            return analysis

        results = {
            'timestamp': datetime.now(),
            'total_articles': analysis['total_articles'],
            'sources': analysis['sources'],
            'important_news': analysis['top_articles'][:5],  # Топ-5 важных новостей
            'sentiment': self._determine_sentiment(analysis)
        }

        return results

    def _determine_sentiment(self, analysis: Dict[str, Any]) -> str:
        """Определение общего настроения новостей"""
        # Здесь можно добавить более сложную логику определения настроения
        if len(analysis['top_articles']) > 0:
            return "positive" if len(analysis['top_articles']) > 5 else "neutral"
        return "neutral"

    def _analyze_news(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ новостей"""
        if news_data['status'] != 'success':
            return {'status': 'error', 'message': 'Нет данных для анализа'}

        self.communicator.say("Анализирую новостной фон...")
        
        # Стандартный анализ ключевых слов
        currency = news_data.get('currency', 'BTC')
        keyword_analysis = self.tools.analyze_news(news_data['articles'], currency)
        
        # NLP-анализ тональности с BERT
        self.communicator.say("Выполняю NLP-анализ тональности новостей...")
        sentiment_analysis = self.tools.analyze_sentiment(news_data['articles'], currency)
        
        # Объединяем результаты анализов
        analysis = {**keyword_analysis}
        analysis['sentiment_analysis'] = sentiment_analysis.get('sentiment_analysis', {})
        
        return analysis