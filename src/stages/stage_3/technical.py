# src/stages/stage_3/technical.py

from typing import Dict, List, Any
import logging
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """Анализатор технических индикаторов"""
    
    def __init__(self, tools, memory, communicator):
        self.tools = tools
        self.memory = memory
        self.communicator = communicator

    def analyze(self, currency: str, days: int) -> Dict[str, Any]:
        """Выполнение технического анализа"""
        self.communicator.say("\nНачинаю технический анализ...")
        
        # Получение исторических данных
        price_data = self._get_price_data(currency, days)
        if price_data.get('status') != 'success':
            self.communicator.show_warning(price_data.get('message', 'Ошибка получения данных'))
            return {'status': 'error'}
            
        # Расчет технических индикаторов
        indicators = self._calculate_indicators(price_data['data'])
        
        # Анализ результатов
        analysis_results = self._analyze_indicators(indicators)
        
        return {
            'status': 'success',
            'price_data': price_data,
            'indicators': indicators,
            'analysis': analysis_results,
            'timestamp': datetime.now()
        }

    def _get_price_data(self, currency: str, days: int) -> Dict[str, Any]:
        """Получение исторических данных о ценах"""
        self.communicator.say("Получаю исторические данные...")
        data = self.tools.get_historical_data(currency, days)
        
        # Проверяем количество полученных данных
        if isinstance(data, dict) and 'data' in data:
            df = data['data']
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            return {
                'status': 'error',
                'message': 'Неожиданный формат данных',
                'data': pd.DataFrame()
            }
        
        # Проверка достаточного количества данных
        if len(df) < 14:  # Минимум для RSI
            return {
                'status': 'error',
                'message': f'Недостаточно данных для анализа. Получено {len(df)} свечей, требуется минимум 14.',
                'data': df
            }
        
        return {
            'status': 'success',
            'message': '',
            'data': df
        }

    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Расчет технических индикаторов"""
        self.communicator.say("Рассчитываю технические индикаторы...")
        
        # Копируем DataFrame для расчетов
        data = df.copy()

        # Определяем адаптивные окна в зависимости от количества данных
        window_sma = min(20, max(5, len(data) // 2))
        window_rsi = min(14, max(5, len(data) // 3))
        
        # Используем новые методы из toolkit для расчета индикаторов
        data['SMA_20'] = self.tools.calculate_sma(data['close'], window_sma)
        data['SMA_50'] = self.tools.calculate_sma(data['close'], min(50, max(5, len(data) // 2)))
        data['SMA_200'] = self.tools.calculate_sma(data['close'], min(200, max(5, len(data) // 2)))
        
        # Расчет RSI с использованием нового метода
        data['RSI'] = self.tools.calculate_rsi(data['close'], window_rsi)
        
        # Расчет MACD с использованием нового метода
        macd_data = self.tools.calculate_macd(
            data['close'], 
            fast_period=min(12, max(3, len(data) // 4)),
            slow_period=min(26, max(6, len(data) // 3)),
            signal_period=min(9, max(3, len(data) // 5))
        )
        data['MACD'] = macd_data['macd']
        data['MACD_Signal'] = macd_data['signal']
        data['MACD_Hist'] = macd_data['histogram']
        
        # Расчет Bollinger Bands с использованием нового метода
        bb_data = self.tools.calculate_bollinger_bands(data['close'], window=window_sma)
        data['BB_Middle'] = bb_data['middle']
        data['BB_Upper'] = bb_data['upper']
        data['BB_Lower'] = bb_data['lower']
        data['BB_StdDev'] = data['close'].rolling(window=window_sma).std()
        
        # Расчет волатильности
        data['Volatility'] = data['BB_StdDev'] / data['BB_Middle'] * 100
        
        # Расчет тренда (направление SMA)
        data['Trend_SMA_20'] = data['SMA_20'].diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        
        # Заполняем NaN значения вместо их удаления
        data = data.ffill().bfill()  # Используем более современный синтаксис

        if data.empty:
            return {
                'dataframe': data,
                'current': {},
                'last_close': float(df['close'].iloc[-1]) if not df.empty else 0,
                'last_rsi': 50,
                'last_macd': 0,
                'last_macd_signal': 0,
                'last_volatility': 0
            }
        
        # Получаем текущие значения
        current = data.iloc[-1].to_dict()
        
        return {
            'dataframe': data,
            'current': current,
            'last_close': float(current['close']),
            'last_rsi': float(current['RSI']),
            'last_macd': float(current['MACD']),
            'last_macd_signal': float(current['MACD_Signal']),
            'last_volatility': float(current['Volatility'])
        }

    def _analyze_indicators(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ технических индикаторов"""
        self.communicator.say("Анализирую технические индикаторы...")
        
        current = indicators['current']
        df = indicators['dataframe']
        
        # Определение тренда
        trend = "боковой"
        if current['SMA_20'] > current['SMA_50']:
            trend = "восходящий"
        elif current['SMA_20'] < current['SMA_50']:
            trend = "нисходящий"
            
        # Анализ RSI
        rsi_signal = "нейтральный"
        if current['RSI'] > 70:
            rsi_signal = "перекуплен"
        elif current['RSI'] < 30:
            rsi_signal = "перепродан"
            
        # Анализ MACD
        macd_signal = "нейтральный"
        if current['MACD'] > current['MACD_Signal']:
            macd_signal = "бычий"
        else:
            macd_signal = "медвежий"
            
        # Анализ Bollinger Bands
        bb_signal = "нейтральный"
        if current['close'] > current['BB_Upper']:
            bb_signal = "перекуплен"
        elif current['close'] < current['BB_Lower']:
            bb_signal = "перепродан"
            
        # Общий сигнал
        signals = {
            "тренд": trend,
            "RSI": rsi_signal,
            "MACD": macd_signal,
            "Bollinger": bb_signal
        }
        
        bull_count = sum(1 for signal in signals.values() if signal in ["восходящий", "бычий", "перепродан"])
        bear_count = sum(1 for signal in signals.values() if signal in ["нисходящий", "медвежий", "перекуплен"])
        
        overall_signal = "нейтральный"
        if bull_count > bear_count + 1:
            overall_signal = "сильный бычий"
        elif bull_count > bear_count:
            overall_signal = "умеренно бычий"
        elif bear_count > bull_count + 1:
            overall_signal = "сильный медвежий"
        elif bear_count > bull_count:
            overall_signal = "умеренно медвежий"
            
        return {
            "trend": trend,
            "signals": signals,
            "overall_signal": overall_signal,
            "support_levels": self._find_support_levels(df),
            "resistance_levels": self._find_resistance_levels(df)
        }

    def _find_support_levels(self, df: pd.DataFrame, window: int = 10) -> List[float]:
        """Определение уровней поддержки"""
        closes = df['close'].values
        lows = df['low'].values
        
        support_levels = []
        for i in range(window, len(lows) - window):
            if all(lows[i] <= lows[i-j] for j in range(1, window+1)) and \
               all(lows[i] <= lows[i+j] for j in range(1, window+1)):
                support_levels.append(lows[i])
                
        # Объединяем близкие уровни
        if support_levels:
            tolerance = np.mean(support_levels) * 0.01  # 1% от среднего
            filtered_levels = [support_levels[0]]
            for level in support_levels[1:]:
                if all(abs(level - prev) > tolerance for prev in filtered_levels):
                    filtered_levels.append(level)
                    
            # Сортируем и берем 3 ближайших уровня ниже текущей цены
            current_price = closes[-1]
            below_price = [level for level in filtered_levels if level < current_price]
            below_price.sort(reverse=True)
            return below_price[:3]
            
        return []

    def _find_resistance_levels(self, df: pd.DataFrame, window: int = 10) -> List[float]:
        """Определение уровней сопротивления"""
        closes = df['close'].values
        highs = df['high'].values
        
        resistance_levels = []
        for i in range(window, len(highs) - window):
            if all(highs[i] >= highs[i-j] for j in range(1, window+1)) and \
               all(highs[i] >= highs[i+j] for j in range(1, window+1)):
                resistance_levels.append(highs[i])
                
        # Объединяем близкие уровни
        if resistance_levels:
            tolerance = np.mean(resistance_levels) * 0.01  # 1% от среднего
            filtered_levels = [resistance_levels[0]]
            for level in resistance_levels[1:]:
                if all(abs(level - prev) > tolerance for prev in filtered_levels):
                    filtered_levels.append(level)
                    
            # Сортируем и берем 3 ближайших уровня выше текущей цены
            current_price = closes[-1]
            above_price = [level for level in filtered_levels if level > current_price]
            above_price.sort()
            return above_price[:3]
            
        return []