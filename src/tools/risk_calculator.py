# src/tools/risk_calculator.py

import numpy as np
import pandas as pd
from typing import Dict, Any, List

class RiskCalculator:
    """Класс для расчета метрик риска"""
    
    def __init__(self):
        pass
        
    def calculate_var_monte_carlo(self, 
                                  returns: pd.Series, 
                                  confidence_level: float = 0.95, 
                                  simulations: int = 10000, 
                                  time_horizon: int = 1) -> float:
        """
        Расчет Value at Risk (VaR) методом Монте-Карло
        
        Args:
            returns (pd.Series): Исторические доходности актива
            confidence_level (float): Уровень доверия (по умолчанию 0.95)
            simulations (int): Количество симуляций (по умолчанию 10000)
            time_horizon (int): Горизонт прогноза в днях (по умолчанию 1)
            
        Returns:
            float: Значение VaR
        """
        # Рассчитываем среднее и стандартное отклонение исторических доходностей
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Генерируем случайные доходности по нормальному распределению
        random_returns = np.random.normal(
            mean_return * time_horizon, 
            std_return * np.sqrt(time_horizon), 
            simulations
        )
        
        # Определяем VaR как квантиль (процентиль) распределения
        var = np.percentile(random_returns, 100 * (1 - confidence_level))
        
        return abs(var)  # Возвращаем абсолютное значение
    
    def calculate_volatility(self, returns: pd.Series) -> float:
        """
        Расчет волатильности
        
        Args:
            returns (pd.Series): Исторические доходности актива
            
        Returns:
            float: Значение волатильности
        """
        return returns.std() * 100  # В процентах
        
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """
        Расчет коэффициента Шарпа
        
        Args:
            returns (pd.Series): Исторические доходности актива
            risk_free_rate (float): Безрисковая ставка (по умолчанию 0.0)
            
        Returns:
            float: Значение коэффициента Шарпа
        """
        excess_returns = returns.mean() - risk_free_rate
        return excess_returns / returns.std() if returns.std() != 0 else 0
    
    def calculate_position_size(self, 
                           capital: float, 
                           max_risk_percent: float, 
                           stop_loss_percent: float, 
                           volatility_percent: float) -> Dict[str, float]:
        """
        Расчет оптимального размера позиции на основе риск-менеджмента
        
        Args:
            capital (float): Доступный капитал
            max_risk_percent (float): Максимальный допустимый риск на сделку (в процентах)
            stop_loss_percent (float): Расстояние до стоп-лосса (в процентах)
            volatility_percent (float): Историческая волатильность (в процентах)
            
        Returns:
            dict: Словарь с размером позиции и другими параметрами
        """
        # Проверка параметров
        if stop_loss_percent <= 0 or volatility_percent <= 0:
            return {
                'position_size': 0,
                'error': 'Некорректные параметры стоп-лосса или волатильности'
            }
        
        # Расчет оптимального размера позиции
        max_risk_amount = capital * (max_risk_percent / 100)
        adjusted_sl = stop_loss_percent * (1 + volatility_percent / 100)  # Корректируем SL с учетом волатильности
        
        # Основная формула
        position_size = max_risk_amount / (adjusted_sl / 100 * capital)
        
        # Расчет денежного эквивалента позиции
        position_value = capital * position_size
        
        # Расчет потенциального убытка при срабатывании стоп-лосса
        potential_loss = position_value * (stop_loss_percent / 100)
        
        # Расчет процента от капитала
        capital_percent = position_size * 100
        
        return {
            'position_size': position_size,  # Доля от капитала (1.0 = 100%)
            'position_value': position_value,  # Денежное выражение
            'capital_percent': capital_percent,  # Процент от капитала
            'potential_loss': potential_loss,  # Возможные потери
            'stop_loss_percent': stop_loss_percent,  # Процент стоп-лосса
            'risk_reward_ratio': 2.0  # Рекомендуемое соотношение риск/прибыль
        }

    def recommend_stop_loss(self, current_price: float, volatility_percent: float) -> Dict[str, float]:
        """
        Рекомендация уровня стоп-лосса на основе волатильности
        
        Args:
            current_price (float): Текущая цена актива
            volatility_percent (float): Историческая волатильность (в процентах)
            
        Returns:
            dict: Словарь с рекомендациями по стоп-лоссу
        """
        # Для волатильных активов стоп-лосс должен быть шире
        # ATR (Average True Range) обычно используется как мера волатильности для установки стоп-лоссов
        
        # Консервативный стоп-лосс: 1.5x волатильность
        conservative_percent = min(volatility_percent * 1.5, 10.0)
        # Агрессивный стоп-лосс: 1x волатильность
        aggressive_percent = volatility_percent
        # Умеренный стоп-лосс: среднее между ними
        moderate_percent = (conservative_percent + aggressive_percent) / 2
        
        # Расчет уровней цены для стоп-лоссов (для длинной позиции)
        conservative_level = current_price * (1 - conservative_percent / 100)
        moderate_level = current_price * (1 - moderate_percent / 100)
        aggressive_level = current_price * (1 - aggressive_percent / 100)
        
        return {
            'conservative': {
                'percent': conservative_percent,
                'price_level': conservative_level
            },
            'moderate': {
                'percent': moderate_percent,
                'price_level': moderate_level
            },
            'aggressive': {
                'percent': aggressive_percent,
                'price_level': aggressive_level
            }
        }