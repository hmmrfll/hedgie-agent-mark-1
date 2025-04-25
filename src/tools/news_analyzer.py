# src/tools/news_analyzer.py

import requests
from typing import Dict, List, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class NewsAnalyzer:
    """Инструмент для работы с новостями"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"
        self.important_keywords = {
            'BTC': [
                'Bitcoin ETF', 'BTC ETF', 'Bitcoin price',
                'Bitcoin regulation', 'Bitcoin SEC', 'BTC price',
                'Bitcoin market', 'Crypto regulation',
                'Bitcoin adoption', 'BTC adoption'
            ],
            'ETH': [
                'Ethereum ETF', 'ETH ETF', 'Ethereum price',
                'Ethereum regulation', 'Ethereum SEC', 'ETH price',
                'Ethereum market', 'ETH market',
                'Ethereum adoption', 'ETH adoption'
            ]
        }

    def get_news(self, currency: str, days: int) -> Dict[str, Any]:
        """Получение новостей за указанный период"""
        try:
            # Формируем параметры запроса
            # Используем объединение всех важных ключевых слов
            all_keywords = [currency] + [kw.split()[0] for kw in self.important_keywords[currency]]
            keywords = ' OR '.join(set(all_keywords))  # убираем дубликаты
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            params = {
                'q': keywords,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'language': 'en',
                'sortBy': 'publishedAt',
                'apiKey': self.api_key
            }

            # Делаем запрос
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Логируем результат
            logger.info(f"Получено {len(data.get('articles', []))} новостей для {currency}")
            
            return {
                'status': 'success',
                'articles': data.get('articles', []),
                'total_results': data.get('totalResults', 0),
                'currency': currency,
                'period': days,
                'timestamp': datetime.now()
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении новостей: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def analyze_sentiment(self, articles: List[Dict], currency: str) -> Dict[str, Any]:
        """Анализ тональности новостей"""
        if not articles:
            return {'status': 'no_data'}

        analysis = {
            'total_articles': len(articles),
            'sources': {},
            'top_articles': [],
            'keywords_found': {keyword: 0 for keyword in self.important_keywords[currency]}
        }

        for article in articles:
            if not isinstance(article, dict):
                continue
            
            source = article.get('source', {})
            source_name = source.get('name', 'Unknown') if isinstance(source, dict) else 'Unknown'
            analysis['sources'][source_name] = analysis['sources'].get(source_name, 0) + 1

            # Проверяем важность статьи
            if self._is_important_article(article, currency):
                article_data = {
                    'title': article.get('title', 'No title'),
                    'source': source_name,
                    'url': article.get('url', ''),
                    'publishedAt': article.get('publishedAt', ''),
                    'content': article.get('description', 'No content')[:200] + '...'  # Добавляем краткое содержание
                }
                analysis['top_articles'].append(article_data)

                # Подсчитываем упоминания ключевых слов
                for keyword in self.important_keywords[currency]:
                    if keyword.lower() in article_data['title'].lower() or \
                       keyword.lower() in article_data['content'].lower():
                        analysis['keywords_found'][keyword] += 1

        # Сортируем топ-статьи по дате
        analysis['top_articles'].sort(
            key=lambda x: x.get('publishedAt', ''),
            reverse=True
        )

        # Определяем общий sentiment на основе найденных ключевых слов
        analysis['sentiment'] = self._calculate_sentiment(analysis['keywords_found'])

        return analysis

    def _is_important_article(self, article: Dict, currency: str) -> bool:
        """Определение важности статьи для конкретной криптовалюты"""
        title = article.get('title', '') or ''
        description = article.get('description', '') or ''
        
        # Объединяем текст для поиска
        full_text = f"{title} {description}".lower()
        
        # Проверяем наличие важных ключевых слов для данной валюты
        for keyword in self.important_keywords[currency]:
            if keyword.lower() in full_text:
                return True
                
        return False
    
    def _calculate_sentiment(self, keywords_found: Dict[str, int]) -> str:
        """Расчет общего настроения на основе найденных ключевых слов"""
        positive_keywords = ['adoption', 'ETF', 'price']
        negative_keywords = ['regulation', 'SEC']
        
        positive_count = sum(count for keyword, count in keywords_found.items() 
                           if any(pos in keyword.lower() for pos in positive_keywords))
        negative_count = sum(count for keyword, count in keywords_found.items() 
                           if any(neg in keyword.lower() for neg in negative_keywords))
        
        if positive_count > negative_count * 2:
            return "strongly positive"
        elif positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count * 2:
            return "negative"
        elif negative_count > positive_count:
            return "slightly negative"
        return "neutral"