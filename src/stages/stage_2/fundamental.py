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

        # Проверка на пустоту или ошибку
        if news_data is None or news_data.get('status') != 'success':
            return {
                'status': 'error',
                'message': 'Ошибка получения новостей',
                'total_articles': 0,
                'important_news': [],
                'sentiment': 'neutral',
                'sentiment_analysis': {}
            }

        # Анализ новостей
        news_analysis = self._analyze_news(news_data)

        # Подготовка результатов
        results = self._prepare_results(news_analysis)

        return results

    def _collect_news(self, currency: str, days: int) -> Dict[str, Any]:
        """Сбор новостей"""
        self.communicator.say("Получаю новости...")
        news = self.tools.get_news(currency, days)

        if news and news.get('status') == 'success':
            self.communicator.say(f"Найдено {news.get('total_results', 0)} новостей")
        else:
            self.communicator.show_warning("Проблемы при получении новостей")

        return news

    def _analyze_news(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ новостей"""
        if not news_data or news_data.get('status') != 'success':
            return {
                'status': 'error',
                'message': 'Нет данных для анализа',
                'total_articles': 0,
                'sources': {},
                'top_articles': [],
                'sentiment_analysis': {}
            }

        self.communicator.say("Анализирую новостной фон...")

        # Безопасно получаем статьи
        articles = news_data.get('articles', []) or []
        currency = news_data.get('currency', 'BTC')  # получаем валюту из новостных данных

        # Стандартный анализ ключевых слов (с проверкой на None)
        keyword_analysis = self.tools.analyze_news(articles, currency) or {}

        # NLP-анализ тональности с BERT (с проверкой на None)
        self.communicator.say("Выполняю NLP-анализ тональности новостей...")
        sentiment_analysis = self.tools.analyze_sentiment(articles, currency) or {}

        # Объединяем результаты анализов с надежными проверками на None
        analysis = {
            'status': keyword_analysis.get('status', 'success'),
            'total_articles': keyword_analysis.get('total_articles', 0),
            'sources': keyword_analysis.get('sources', {}),
            'top_articles': keyword_analysis.get('top_articles', []),
            'sentiment_analysis': sentiment_analysis.get('sentiment_analysis', {})
        }

        # Проверяем необходимые ключи
        if 'sentiment' not in analysis:
            analysis['sentiment'] = self._determine_sentiment(analysis)

        return analysis

    def _prepare_results(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовка результатов анализа"""
        # Эта проверка гарантирует, что у нас всегда будет корректный словарь
        analysis = analysis or {}

        if analysis.get('status') == 'error':
            default_result = {
                'status': 'error',
                'message': analysis.get('message', 'Ошибка анализа'),
                'timestamp': datetime.now(),
                'total_articles': 0,
                'sources': {},
                'important_news': [],
                'sentiment': 'neutral',
                'sentiment_analysis': {}
            }
            return default_result

        # Безопасно получаем необходимые данные с дефолтными значениями
        results = {
            'timestamp': datetime.now(),
            'status': 'success',
            'total_articles': analysis.get('total_articles', 0),
            'sources': analysis.get('sources', {}),
            'important_news': (analysis.get('top_articles', []) or [])[:5],  # Топ-5 важных новостей
            'sentiment': self._determine_sentiment(analysis),
            'sentiment_analysis': analysis.get('sentiment_analysis', {})
        }

        return results

    def _determine_sentiment(self, analysis: Dict[str, Any]) -> str:
        """Определение общего настроения новостей"""
        # Проверяем, существует ли analysis и top_articles в нем
        analysis = analysis or {}
        top_articles = analysis.get('top_articles', []) or []

        if len(top_articles) > 5:
            return "positive"
        elif len(top_articles) > 0:
            return "neutral"
        return "neutral"
