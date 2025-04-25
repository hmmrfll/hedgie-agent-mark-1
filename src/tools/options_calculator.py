# src/tools/options_calculator.py

import math
from datetime import datetime
from scipy.stats import norm
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

@dataclass
class OptionMetrics:
    """Класс для хранения метрик опциона"""
    delta: float
    current_price: float
    strike: float
    days_to_expiry: float
    volatility: float
    option_type: str
    rate: float = 0.05  # Безрисковая ставка по умолчанию 5%

class OptionsCalculator:
    """Инструмент для расчета опционных параметров"""
    
    def __init__(self, rate: float = 0.05):
        self.rate = rate

    def calculate_delta(self, 
                       current_price: float,
                       strike: float,
                       expiry_date: datetime,
                       volatility: float,
                       option_type: str) -> Optional[OptionMetrics]:
        """
        Расчет дельты опциона по модели Блэка-Шоулза

        Args:
            current_price: Текущая цена актива
            strike: Цена страйка
            expiry_date: Дата экспирации
            volatility: Волатильность (в процентах)
            option_type: Тип опциона ('C' для колл, 'P' для пут)

        Returns:
            OptionMetrics: объект с метриками опциона
        """
        try:
            # Проверка входных данных
            if not all([current_price, strike, expiry_date, volatility]):
                logger.warning("Неполные данные для расчета дельты")
                return None

            # Расчет времени до экспирации в годах
            days_to_expiry = (expiry_date - datetime.now()).days
            T = days_to_expiry / 365.0

            if T <= 0:
                logger.warning("Опцион истек или истекает сегодня")
                return None

            # Приведение волатильности к десятичному формату
            sigma = volatility / 100 if volatility > 1 else volatility

            # Расчет d1 по формуле Блэка-Шоулза
            d1 = (math.log(current_price / strike) + 
                  (self.rate + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

            # Расчет дельты в зависимости от типа опциона
            if option_type == 'C':
                delta = norm.cdf(d1)
            elif option_type == 'P':
                delta = norm.cdf(d1) - 1
            else:
                logger.error(f"Неизвестный тип опциона: {option_type}")
                return None

            return OptionMetrics(
                delta=delta,
                current_price=current_price,
                strike=strike,
                days_to_expiry=days_to_expiry,
                volatility=volatility,
                option_type=option_type,
                rate=self.rate
            )

        except Exception as e:
            logger.error(f"Ошибка расчета дельты: {e}")
            return None

    def validate_inputs(self, 
                       current_price: float,
                       strike: float,
                       volatility: float) -> bool:
        """Проверка входных данных"""
        if current_price <= 0:
            logger.error("Текущая цена должна быть положительной")
            return False
        if strike <= 0:
            logger.error("Цена страйка должна быть положительной")
            return False
        if volatility <= 0:
            logger.error("Волатильность должна быть положительной")
            return False
        return True