# src/tools/price_data.py

import requests
import pandas as pd
from typing import Dict, List, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PriceDataFetcher:
    """Инструмент для получения исторических данных о ценах"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        self.symbols = {
            'BTC': 'BTCUSDT',
            'ETH': 'ETHUSDT'
        }
        self.intervals = {
            '1d': '1 день',
            '4h': '4 часа',
            '1h': '1 час'
        }

    def get_historical_data(self, currency: str, days: int, interval: str = '1d') -> Dict[str, Any]:
        """Получение исторических данных OHLCV"""
        try:
            symbol = self.symbols.get(currency)
            if not symbol:
                return {'status': 'error', 'message': f'Неподдерживаемая валюта: {currency}'}
                
            if interval not in self.intervals:
                interval = '1d'
                
            # Рассчитываем временные границы
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            
            # Параметры запроса
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': start_time,
                'endTime': end_time,
                'limit': 1000  # максимальное количество свечей
            }
            
            # Выполняем запрос
            response = requests.get(f"{self.base_url}/klines", params=params)
            response.raise_for_status()
            
            # Преобразуем данные в DataFrame
            data = response.json()
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignored'
            ])
            
            # Преобразуем типы данных
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            logger.info(f"Получено {len(df)} свечей {interval} для {currency}")
            
            return {
                'status': 'success',
                'data': df,
                'currency': currency,
                'interval': interval,
                'days': days
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении исторических данных: {e}")
            return {
                'status': 'error',
                'message': f'Ошибка: {str(e)}'
            }