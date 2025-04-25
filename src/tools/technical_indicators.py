# src/tools/technical_indicators.py

import pandas as pd
import numpy as np

class TechnicalIndicators:
    """Класс для расчета технических индикаторов"""
    
    def __init__(self):
        pass
        
    def calculate_rsi(self, prices, window=14):
        """
        Расчет индекса относительной силы (RSI)
        
        Args:
            prices (pd.Series): Серия цен закрытия
            window (int): Период для расчета RSI (по умолчанию 14)
            
        Returns:
            pd.Series: Серия значений RSI
        """
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window).mean()
        loss = -delta.where(delta < 0, 0).rolling(window).mean()
        
        # Обрабатываем случай деления на ноль
        rs = gain / loss.replace(0, np.finfo(float).eps)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_sma(self, prices, window):
        """
        Расчет простой скользящей средней (SMA)
        
        Args:
            prices (pd.Series): Серия цен закрытия
            window (int): Период для расчета SMA
            
        Returns:
            pd.Series: Серия значений SMA
        """
        return prices.rolling(window=window).mean()
    
    def calculate_ema(self, prices, window):
        """
        Расчет экспоненциальной скользящей средней (EMA)
        
        Args:
            prices (pd.Series): Серия цен закрытия
            window (int): Период для расчета EMA
            
        Returns:
            pd.Series: Серия значений EMA
        """
        return prices.ewm(span=window, adjust=False).mean()
    
    def calculate_macd(self, prices, fast_period=12, slow_period=26, signal_period=9):
        """
        Расчет индикатора MACD
        
        Args:
            prices (pd.Series): Серия цен закрытия
            fast_period (int): Период быстрой EMA (по умолчанию 12)
            slow_period (int): Период медленной EMA (по умолчанию 26)
            signal_period (int): Период сигнальной линии (по умолчанию 9)
            
        Returns:
            dict: Словарь с MACD, сигнальной линией и гистограммой
        """
        fast_ema = self.calculate_ema(prices, fast_period)
        slow_ema = self.calculate_ema(prices, slow_period)
        
        macd_line = fast_ema - slow_ema
        signal_line = self.calculate_ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_bollinger_bands(self, prices, window=20, num_std=2):
        """
        Расчет полос Боллинджера
        
        Args:
            prices (pd.Series): Серия цен закрытия
            window (int): Период для расчета (по умолчанию 20)
            num_std (int): Количество стандартных отклонений (по умолчанию 2)
            
        Returns:
            dict: Словарь с верхней, средней и нижней полосами
        """
        middle_band = self.calculate_sma(prices, window)
        std_dev = prices.rolling(window=window).std()
        
        upper_band = middle_band + (std_dev * num_std)
        lower_band = middle_band - (std_dev * num_std)
        
        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        }