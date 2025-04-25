# src/stages/stage_4/risk_management.py

from typing import Dict, List, Any
import logging
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskManagementAnalyzer:
    """Анализатор риск-менеджмента"""
    
    def __init__(self, tools, memory, communicator):
        self.tools = tools
        self.memory = memory
        self.communicator = communicator

    def analyze(self, currency: str, days: int) -> Dict[str, Any]:
        """Выполнение анализа рисков"""
        self.communicator.say("\nНачинаю анализ рисков...")
        
        # Получение исторических данных
        price_data = self._get_price_data(currency, days)
        if price_data.get('status') != 'success':
            self.communicator.show_warning(price_data.get('message', 'Ошибка получения данных'))
            return {'status': 'error'}
            
        # Расчет метрик риска
        risk_metrics = self._calculate_risk_metrics(price_data['data'])
        
        # Анализ результатов
        risk_assessment = self._analyze_risk(risk_metrics)
        
        return {
            'status': 'success',
            'price_data': price_data,
            'risk_metrics': risk_metrics,
            'risk_assessment': risk_assessment,
            'timestamp': datetime.now()
        }

    def _get_price_data(self, currency: str, days: int) -> Dict[str, Any]:
        """Получение исторических данных о ценах"""
        self.communicator.say("Получаю исторические данные для расчета рисков...")
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
        if len(df) < 14:  # Минимум для надежных расчетов
            return {
                'status': 'error',
                'message': f'Недостаточно данных для анализа рисков. Получено {len(df)} свечей, требуется минимум 14.',
                'data': df
            }
        
        return {
            'status': 'success',
            'message': '',
            'data': df
        }

    def _calculate_risk_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Расчет метрик риска"""
        self.communicator.say("Рассчитываю метрики риска...")
        
        # Получаем цены закрытия
        close_prices = df['close']
        
        # Рассчитываем доходности
        returns = close_prices.pct_change().dropna()
        
        # Запускаем симуляцию Монте-Карло для VaR
        self.communicator.say("Выполняю симуляцию Монте-Карло для расчета VaR...")
        var_95 = self.tools.calculate_var_monte_carlo(returns, confidence_level=0.95) * 100  # В процентах
        var_99 = self.tools.calculate_var_monte_carlo(returns, confidence_level=0.99) * 100  # В процентах
        
        # Рассчитываем другие метрики риска
        volatility = self.tools.calculate_volatility(returns)
        sharpe_ratio = self.tools.calculate_sharpe_ratio(returns)
        
        # Симуляция для разных временных горизонтов
        var_5d_95 = self.tools.calculate_var_monte_carlo(returns, confidence_level=0.95, time_horizon=5) * 100
        var_10d_95 = self.tools.calculate_var_monte_carlo(returns, confidence_level=0.95, time_horizon=10) * 100
        
        current_price = close_prices.iloc[-1]
    
        # Параметры для расчета (можно настроить)
        capital = 10000  # Пример капитала в USD
        max_risk_percent = 2.0  # Максимальный риск на сделку (%)
        
        # Рекомендуемые стоп-лоссы
        stop_loss_recommendations = self.tools.recommend_stop_loss(current_price, volatility)
        
        # Расчет позиции для разных уровней риска
        position_conservative = self.tools.calculate_position_size(
            capital, max_risk_percent, 
            stop_loss_recommendations['conservative']['percent'], volatility
        )
        
        position_moderate = self.tools.calculate_position_size(
            capital, max_risk_percent, 
            stop_loss_recommendations['moderate']['percent'], volatility
        )
        
        position_aggressive = self.tools.calculate_position_size(
            capital, max_risk_percent, 
            stop_loss_recommendations['aggressive']['percent'], volatility
        )
        # Результаты расчетов
        risk_metrics = {
            'var_95': var_95,
            'var_99': var_99,
            'var_5d_95': var_5d_95,
            'var_10d_95': var_10d_95,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'current_price': close_prices.iloc[-1],
            'investment_example': 10000,  # Пример инвестиции в USD
            'potential_loss_95': 10000 * (var_95 / 100),  # Потенциальные потери в USD
            'current_price': current_price,
            'investment_example': capital,
            'potential_loss_95': capital * (var_95 / 100),
            'stop_loss': stop_loss_recommendations,
            'position_sizing': {
                        'conservative': position_conservative,
                        'moderate': position_moderate,
                        'aggressive': position_aggressive
                    }       
        }
        
        return risk_metrics

    def _analyze_risk(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """Анализ результатов расчета рисков"""
        self.communicator.say("Анализирую результаты расчета рисков...")
        
        var_95 = metrics['var_95']
        volatility = metrics['volatility']
        sharpe_ratio = metrics['sharpe_ratio']
        
        # Определение уровня риска
        if var_95 < 3:
            risk_level = "низкий"
        elif var_95 < 7:
            risk_level = "средний"
        else:
            risk_level = "высокий"
        
        # Оценка волатильности
        if volatility < 2:
            volatility_assessment = "низкая"
        elif volatility < 5:
            volatility_assessment = "средняя"
        else:
            volatility_assessment = "высокая"
        
        # Оценка соотношения риск/доходность
        if sharpe_ratio < 0.5:
            sharpe_assessment = "неблагоприятное"
        elif sharpe_ratio < 1.0:
            sharpe_assessment = "среднее"
        else:
            sharpe_assessment = "благоприятное"
        
        position_sizing = metrics.get('position_sizing', {})
        moderate_position = position_sizing.get('moderate', {})
        
        if moderate_position:
            position_percent = moderate_position.get('capital_percent', 0)
            if position_percent > 50:
                position_assessment = "очень крупная"
                position_recommendation = "Размер позиции крайне велик. Рекомендуется снизить риск или дробить позицию."
            elif position_percent > 25:
                position_assessment = "крупная"
                position_recommendation = "Размер позиции значителен. Рассмотрите возможность частичного входа."
            elif position_percent > 10:
                position_assessment = "умеренная"
                position_recommendation = "Разумный размер позиции."
            else:
                position_assessment = "консервативная"
                position_recommendation = "Консервативный размер позиции. Возможно увеличение при благоприятных условиях."
        else:
            position_assessment = "не определена"
            position_recommendation = "Не удалось рассчитать оптимальный размер позиции."
        
        # Формируем итоговую оценку
        assessment = {
            'risk_level': risk_level,
            'volatility_assessment': volatility_assessment,
            'sharpe_assessment': sharpe_assessment,
            'summary': f"Уровень риска: {risk_level}, волатильность: {volatility_assessment}, соотношение риск/доходность: {sharpe_assessment}",
            'recommendation': self._generate_recommendation(risk_level, sharpe_ratio),
            'position_assessment': position_assessment,
            'position_recommendation': position_recommendation,
            'summary': f"Уровень риска: {risk_level}, волатильность: {volatility_assessment}, размер позиции: {position_assessment}",
            'recommendation': self._generate_recommendation(risk_level, sharpe_ratio, position_assessment)
        }
        
        return assessment
    
    def _generate_recommendation(self, risk_level: str, sharpe_ratio: float, position_assessment: str = "не определена") -> str:
        """Генерация рекомендации по управлению рисками с учетом размера позиции"""
        # Определяем базовую рекомендацию на основе риска и коэффициента Шарпа
        if risk_level == "низкий" and sharpe_ratio > 0.8:
            base_recommendation = "Благоприятное соотношение риск/доходность. Можно наращивать позицию."
        elif risk_level == "высокий" and sharpe_ratio < 0.5:
            base_recommendation = "Неблагоприятное соотношение риск/доходность. Рекомендуется сокращение позиции или хеджирование."
        elif risk_level == "высокий":
            base_recommendation = "Высокий риск. Рекомендуется установить стоп-лосс или использовать опционную защиту."
        elif risk_level == "средний":
            base_recommendation = "Средний уровень риска. Рекомендуется диверсификация портфеля."
        else:
            base_recommendation = "Низкий уровень риска. Можно сохранять текущую позицию."
        
        # Добавляем рекомендации по размеру позиции
        if position_assessment == "очень крупная":
            if risk_level == "высокий":
                position_advice = " Настоятельно рекомендуется уменьшить размер позиции или разбить вход на несколько частей."
            else:
                position_advice = " Рекомендуется уменьшить размер позиции или использовать поэтапный вход."
        elif position_assessment == "крупная":
            if risk_level == "высокий":
                position_advice = " Размер позиции значителен для данного уровня риска. Рассмотрите возможность частичного входа или хеджирования."
            else:
                position_advice = " Размер позиции значителен, рассмотрите частичный вход для снижения рисков."
        elif position_assessment == "умеренная":
            position_advice = " Размер позиции сбалансирован относительно риска."
        elif position_assessment == "консервативная":
            if risk_level == "низкий" and sharpe_ratio > 0.8:
                position_advice = " При желании возможно увеличение позиции с сохранением правил риск-менеджмента."
            else:
                position_advice = " Консервативный размер позиции соответствует текущим рыночным условиям."
        else:
            position_advice = ""
        
        # Добавляем советы по тейк-профиту на основе соотношения риск/доходность
        if sharpe_ratio > 1.0:
            tp_advice = " Рекомендуемое соотношение риск/прибыль: минимум 1:3."
        elif sharpe_ratio > 0.5:
            tp_advice = " Рекомендуемое соотношение риск/прибыль: минимум 1:2."
        else:
            tp_advice = " Рекомендуемое соотношение риск/прибыль: не менее 1:1.5."
        
        # Формируем итоговую рекомендацию
        final_recommendation = base_recommendation + position_advice
        
        # Добавляем совет по тейк-профиту, если оценка размера позиции определена
        if position_assessment != "не определена":
            final_recommendation += tp_advice
        
        return final_recommendation
            