# src/stages/stage_5/recommendations.py

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class RecommendationGenerator:
    """Генератор рекомендаций и отчетов"""
    
    def __init__(self, tools, memory, communicator):
        self.tools = tools
        self.memory = memory
        self.communicator = communicator

    def generate(self, currency: str, days: int) -> Dict[str, Any]:
        """Генерация рекомендаций и отчета"""
        self.communicator.say("\nФормирую итоговые рекомендации и отчет...")
        
        # Получаем результаты предыдущих этапов из памяти
        context = self.memory.get_context()
        block_trades = context.get('block_trades_analysis', {})
        fundamental = context.get('fundamental_analysis', {})
        technical = context.get('technical_analysis', {})
        risk = context.get('risk_management', {})
        
        # Формируем общие рекомендации
        recommendations = self._prepare_recommendations(
            currency, days, block_trades, fundamental, technical, risk
        )

        telegram_sent = self.tools.send_telegram_report(recommendations)
        if telegram_sent:
            self.communicator.say("\nОтчет успешно отправлен в Telegram!")
        
        # Генерируем отчет в формате LaTeX
        report_path = self._generate_report(recommendations)
    
        
        return {
            'status': 'success',
            'recommendations': recommendations,
            'report_path': report_path,
            'timestamp': datetime.now()
        }
    
    def _prepare_recommendations(self, 
                       currency: str, 
                       days: int, 
                       block_trades: Dict[str, Any], 
                       fundamental: Dict[str, Any],
                       technical: Dict[str, Any],
                       risk: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовка данных для рекомендаций"""
        # Создаем пустой словарь рекомендаций
        recommendations = {}
        
        # Текущая цена
        current_price = technical.get('indicators', {}).get('last_close', 0)
        
        # Анализ настроения рынка
        technical_sentiment = technical.get('analysis', {}).get('overall_signal', 'нейтральный')
        option_sentiment = "бычье" if block_trades.get('total_delta', 0) > 100 else "медвежье" if block_trades.get('total_delta', 0) < -100 else "нейтральное"
        news_sentiment = fundamental.get('sentiment', 'neutral')
        
        # Общая рекомендация
        sentiments = [technical_sentiment, option_sentiment, news_sentiment]
        bull_count = sum(1 for s in sentiments if "быч" in s or "восходящ" in s)
        bear_count = sum(1 for s in sentiments if "медвеж" in s or "нисходящ" in s)
        
        if bull_count >= 2:
            action = "ПОКУПАТЬ"
            recommendation = "ПОКУПАТЬ - большинство индикаторов указывают на рост"
        elif bear_count >= 2:
            action = "ПРОДАВАТЬ"
            recommendation = "ПРОДАВАТЬ - большинство индикаторов указывают на снижение"
        else:
            action = "ДЕРЖАТЬ"
            recommendation = "ДЕРЖАТЬ - сигналы смешанные, требуется дополнительный анализ"
        
        # Риск-менеджмент
        risk_level = risk.get('risk_assessment', {}).get('risk_level', 'не определен')
        risk_summary = risk.get('risk_assessment', {}).get('summary', '')
        risk_recommendation = risk.get('risk_assessment', {}).get('recommendation', '')
        
        risk_metrics = risk.get('risk_metrics', {})
        var_95 = risk_metrics.get('var_95', 0)
        var_5d = risk_metrics.get('var_5d_95', 0)
        var_10d = risk_metrics.get('var_10d_95', 0)
        volatility = risk_metrics.get('volatility', 0)
        sharpe_ratio = risk_metrics.get('sharpe_ratio', 0)
        
        # Рекомендации по стоп-лоссу и тейк-профиту
        stop_loss = risk_metrics.get('stop_loss', {}).get('moderate', {})
        sl_percent = stop_loss.get('percent', 5.0)
        sl_price = current_price * (1 - sl_percent / 100)
        
        # Тейк-профит на основе соотношения риск/прибыль
        risk_reward_ratio = 2.0  # По умолчанию 1:2
        tp_percent = sl_percent * risk_reward_ratio
        tp_price = current_price * (1 + tp_percent / 100)
        
        # Размер позиции
        position = risk_metrics.get('position_sizing', {}).get('moderate', {})
        position_percent = position.get('capital_percent', 0)
        position_value = position.get('position_value', 0)
        
        # Формируем стратегию входа
        if action == "ПОКУПАТЬ":
            entry_strategy = f"Покупка по текущей цене ${current_price:.2f} или при откате к уровню поддержки"
        elif action == "ПРОДАВАТЬ":
            entry_strategy = f"Продажа по текущей цене ${current_price:.2f} или при отскоке к уровню сопротивления"
        else:
            entry_strategy = "Ожидание более четких сигналов перед входом в позицию"
        
        # Ключевые новости
        key_news = []
        for news in fundamental.get('important_news', [])[:3]:
            key_news.append(f"{news.get('title', '')} ({news.get('source', '')})")
        
        # Основные стратегии опционной торговли
        strategies_data = {}
        for strategy_type, count in block_trades.get('strategy_analysis', {}).get('stats', {}).get('by_type', {}).items():
            volume = block_trades.get('strategy_analysis', {}).get('stats', {}).get('volume_by_type', {}).get(strategy_type, 0)
            strategies_data[strategy_type] = volume
        
        main_strategies = ", ".join([f"{s} ({v:.1f})" for s, v in sorted(strategies_data.items(), key=lambda x: x[1], reverse=True)[:3]])
        
        # Итоговая рекомендация с учетом всех факторов
        conclusion = f"""
    На основе комплексного анализа рынка криптовалюты {currency} за последние {days} дней, 
    предлагается следующая торговая стратегия:

    1. Рекомендуемое действие: {action}
    {recommendation}

    2. Технический анализ показывает {technical_sentiment} настроение, RSI: {technical.get('indicators', {}).get('last_rsi', 0):.2f}

    3. Анализ опционов указывает на {option_sentiment} настроение рынка с дельтой {block_trades.get('total_delta', 0):.2f}

    4. Общий новостной фон: {news_sentiment}

    5. Уровень риска: {risk_level}
    {risk_recommendation}

    6. Стратегия управления позицией:
    - Рекомендуемый размер: {position_percent:.2f}% от капитала
    - Стоп-лосс: ${sl_price:.2f} ({sl_percent:.2f}%)
    - Тейк-профит: ${tp_price:.2f} ({tp_percent:.2f}%)
    - Соотношение риск/прибыль: 1:{risk_reward_ratio}

    При изменении рыночных условий рекомендуется пересмотреть стратегию.
    """
        
        # Добавляем данные по опционам
        recommendations['calls_count'] = block_trades.get('calls_count', 0)
        recommendations['puts_count'] = block_trades.get('puts_count', 0)
        recommendations['call_volume'] = f"{block_trades.get('call_volume', 0):.2f}"
        recommendations['put_volume'] = f"{block_trades.get('put_volume', 0):.2f}"
        
        # Опционный сентимент
        recommendations['option_sentiment'] = option_sentiment
        
        # Крупнейшие сделки
        largest_trades = []
        for trade in block_trades.get('strategy_analysis', {}).get('stats', {}).get('largest_trades', [])[:5]:
            largest_trades.append({
                'type': trade.get('type', 'Unknown'),
                'amount': trade.get('amount', 0),
                'trade_id': trade.get('combo_id', trade.get('trade_id', 'N/A'))
            })
        recommendations['largest_trades'] = largest_trades
        
        # Формируем остальной словарь с рекомендациями для отчета
        recommendations.update({
            'currency': currency,
            'days': days,
            'report_date': datetime.now().strftime("%d.%m.%Y"),
            'current_price': f"{current_price:.2f}",
            'recommendation': action,
            'risk_level': risk_level,
            
            'total_trades': block_trades.get('total_trades', 0),
            'call_put_ratio': f"{block_trades.get('call_volume', 0) / block_trades.get('put_volume', 1):.2f}",
            'total_delta': f"{block_trades.get('total_delta', 0):.2f}",
            'main_strategies': main_strategies,
            'strategies_data': strategies_data,
            
            'trend': technical.get('analysis', {}).get('trend', 'неопределенный'),
            'rsi_value': f"{technical.get('indicators', {}).get('last_rsi', 0):.2f}",
            'rsi_signal': technical.get('analysis', {}).get('signals', {}).get('RSI', 'нейтральный'),
            'macd_signal': technical.get('analysis', {}).get('signals', {}).get('MACD', 'нейтральный'),
            'technical_signal': technical_sentiment,
            
            'news_count': fundamental.get('total_articles', 0),
            'news_sentiment': news_sentiment,
            'key_news': "; ".join(key_news),
            
            'var_value': f"{var_95:.2f}",
            'volatility': f"{volatility:.2f}",
            'sharpe_ratio': f"{sharpe_ratio:.2f}",
            'position_size': f"{position_percent:.2f}",
            'stop_loss_price': f"{sl_price:.2f}",
            'stop_loss_percent': f"{sl_percent:.2f}",
            'take_profit_price': f"{tp_price:.2f}",
            'take_profit_percent': f"{tp_percent:.2f}",
            
            'entry_strategy': entry_strategy,
            'risk_reward_ratio': f"{risk_reward_ratio}",
            
            'conclusion': conclusion,
            
            'price_data': technical.get('price_data', {}).get('data', None)
        })
    
        return recommendations

    def _generate_report(self, recommendations: Dict[str, Any]) -> str:
        """Генерация отчета в формате LaTeX"""
        try:
            # Генерируем графики для отчета
            charts = self.tools.generate_charts(recommendations)
            
            # Добавляем пути к графикам в рекомендации
            recommendations.update(charts)
            
            # Путь к шаблону отчета
            template_path = os.path.join(os.getcwd(), 'src', 'templates', 'report_template.tex')
            if not os.path.exists(template_path):
                template_path = None
            
            # Генерируем отчет
            report_path = self.tools.generate_latex_report(recommendations, template_path)
            
            self.communicator.say(f"Отчет сгенерирован и сохранен: {report_path}")
            
            return report_path
        except Exception as e:
            logger.error(f"Ошибка при генерации отчета: {e}")
            self.communicator.show_error(f"Не удалось сгенерировать отчет: {e}")
            return ""