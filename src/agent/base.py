# src/agent/base.py

from typing import Optional, Tuple, Dict, List, Any
import logging
from datetime import datetime

from .states import AgentState
from .memory import Memory
from .communicator import Communicator
from src.tools.toolkit import ToolKit
from src.stages.stage_1.block_trades import BlockTradesAnalyzer
from src.stages.stage_2.fundamental import FundamentalAnalyzer  # Добавляем импорт
from src.stages.stage_3.technical import TechnicalAnalyzer
from src.stages.stage_4.risk_management import RiskManagementAnalyzer  # Добавляем импорт
from src.stages.stage_5.recommendations import RecommendationGenerator  # Добавляем импорт

logger = logging.getLogger(__name__)

class TradingAgent:
    # ... остальной код остается без изменений ...
    def __init__(self, telegram_token: str = None, telegram_chat_ids: List[str] = None):
        """Инициализация агента и его компонентов"""
        self.tools = ToolKit()
        self.state = AgentState.IDLE
        self.memory = Memory()
        self.communicator = Communicator()
        self.tools = ToolKit(
                            telegram_token=telegram_token,
                             telegram_chat_ids=telegram_chat_ids,
                             )


        # Инициализация анализаторов
        self.block_trades_analyzer = BlockTradesAnalyzer(
            self.tools,
            self.memory,
            self.communicator
        )
        self.fundamental_analyzer = FundamentalAnalyzer(
            self.tools,
            self.memory,
            self.communicator
        )
        self.technical_analyzer = TechnicalAnalyzer(
            self.tools,
            self.memory,
            self.communicator
        )
        self.risk_management_analyzer = RiskManagementAnalyzer(
            self.tools,
            self.memory,
            self.communicator
        )
        self.recommendation_generator = RecommendationGenerator(
            self.tools,
            self.memory,
            self.communicator
        )

    def get_user_input(self) -> Optional[Tuple[str, int]]:
        """Получение и валидация пользовательского ввода"""
        self.state = AgentState.IDLE

        # Получаем валюту
        currency = self.communicator.ask("Введите валюту ('BTC', 'ETH') или 'exit' для выхода:")
        currency = currency.upper()

        if currency.lower() == 'exit':
            self.communicator.say("Получена команда завершения работы.")
            return None

        if currency not in ['BTC', 'ETH']:
            self.communicator.show_warning("Неподдерживаемая валюта")
            return None

        # Получаем количество дней
        try:
            days = int(self.communicator.ask("Введите количество дней (14-365):"))
            if not 14 <= days <= 365:
                self.communicator.show_warning("Количество дней должно быть не менее 14 для корректного технического анализа")
                return None
        except ValueError:
            self.communicator.show_error("Некорректное значение для количества дней")
            return None

        # Сохраняем параметры в память
        self.memory.update_context({
            'currency': currency,
            'days': days,
            'timestamp': datetime.now()
        })

        return currency, days

    def process_trades(self, currency: str, days: int):
        """Обработка торговых данных"""
        try:
            # Этап 1: Анализ блочных сделок
            self.state = AgentState.BLOCK_TRADES_ANALYSIS
            block_trades_results = self.block_trades_analyzer.analyze(currency, days)

            # Сохраняем результаты в память
            self.memory.update_context({
                'block_trades_analysis': block_trades_results
            })

            # Отображаем результаты
            self._display_block_trades_results(block_trades_results)

            # Этап 2: Фундаментальный анализ
            self.state = AgentState.FUNDAMENTAL_ANALYSIS
            fundamental_results = self.fundamental_analyzer.analyze(currency, days)

            # Сохраняем результаты в память
            self.memory.update_context({
                'fundamental_analysis': fundamental_results
            })

            # Отображаем результаты фундаментального анализа
            self._display_fundamental_results(fundamental_results)

            # Этап 3: Технический анализ
            self.state = AgentState.TECHNICAL_ANALYSIS
            technical_results = self.technical_analyzer.analyze(currency, days)

            # Сохраняем результаты
            self.memory.update_context({
                'technical_analysis': technical_results
            })

            # Отображаем результаты технического анализа
            self._display_technical_results(technical_results)

            # Этап 4: Риск-менеджмент
            self.state = AgentState.RISK_MANAGEMENT
            risk_results = self.risk_management_analyzer.analyze(currency, days)

            # Сохраняем результаты
            self.memory.update_context({
                'risk_management': risk_results
            })

            # Отображаем результаты риск-менеджмента
            self._display_risk_results(risk_results)

            # Формируем общее заключение со всеми этапами
            self._make_final_conclusion(block_trades_results, fundamental_results, technical_results, risk_results)

            self.state = AgentState.RECOMMENDATIONS
            recommendations_results = self.recommendation_generator.generate(currency, days)

            # Сохраняем результаты
            self.memory.update_context({
                'recommendations': recommendations_results
            })

            # Отображаем результаты
            self._display_recommendations(recommendations_results)

        except Exception as e:
            logger.error(f"Ошибка при обработке данных: {e}")
            self.communicator.show_error(f"Произошла ошибка при обработке данных: {e}")

    def _display_results(self, results: Dict[str, Any]):
        """Отображение результатов анализа"""
        if not results or results.get('status') == 'no_data':
            self.communicator.say("Нет данных для анализа")
            return

        # Общая статистика
        self.communicator.say("\nОбщая статистика:")
        self.communicator.say(f"- Всего сделок: {results['total_trades']}")
        self.communicator.say(f"- CALL опционов: {results['calls_count']}")
        self.communicator.say(f"- PUT опционов: {results['puts_count']}")
        self.communicator.say(f"- Общий объем CALL: {results['call_volume']:.2f}")
        self.communicator.say(f"- Общий объем PUT: {results['put_volume']:.2f}")

        # Анализ стратегий
        strategy_analysis = results.get('strategy_analysis', {})
        self.communicator.say("\nАнализ стратегий:")
        for strategy_type, stats in strategy_analysis.get('stats', {}).get('by_type', {}).items():
            volume = strategy_analysis['stats']['volume_by_type'].get(strategy_type, 0)
            self.communicator.say(f"- {strategy_type}: {stats} сделок, объем {volume:.2f}")

        # Крупнейшие сделки
        self.communicator.say("\nКрупнейшие сделки:")
        for trade in strategy_analysis.get('stats', {}).get('largest_trades', []):
            self.communicator.say(
                f"- {trade['type']}: объем {trade['amount']:.2f}, "
                f"ID: {trade['combo_id'] or trade['trade_id']}"
            )

        # Заключение
        self._make_conclusion(results)

    def _display_block_trades_results(self, results: Dict[str, Any]):
        """Отображение результатов анализа блочных сделок"""
        if not results or results.get('status') == 'no_data':
            self.communicator.say("Нет данных для анализа")
            return

        # Общая статистика
        self.communicator.say("\nОбщая статистика:")
        self.communicator.say(f"- Всего сделок: {results['total_trades']}")
        self.communicator.say(f"- CALL опционов: {results['calls_count']}")
        self.communicator.say(f"- PUT опционов: {results['puts_count']}")
        self.communicator.say(f"- Общий объем CALL: {results['call_volume']:.2f}")
        self.communicator.say(f"- Общий объем PUT: {results['put_volume']:.2f}")

        # Анализ стратегий
        strategy_analysis = results.get('strategy_analysis', {})
        self.communicator.say("\nАнализ стратегий:")
        for strategy_type, stats in strategy_analysis.get('stats', {}).get('by_type', {}).items():
            volume = strategy_analysis['stats']['volume_by_type'].get(strategy_type, 0)
            self.communicator.say(f"- {strategy_type}: {stats} сделок, объем {volume:.2f}")

        # Крупнейшие сделки
        self.communicator.say("\nКрупнейшие сделки:")
        for trade in strategy_analysis.get('stats', {}).get('largest_trades', []):
            self.communicator.say(
                f"- {trade['type']}: объем {trade['amount']:.2f}, "
                f"ID: {trade['combo_id'] or trade['trade_id']}"
            )

    def _display_fundamental_results(self, results: Dict[str, Any]):
        """Отображение результатов фундаментального анализа"""
        if results.get('status') == 'error':
            self.communicator.show_warning(results.get('message', 'Ошибка анализа'))
            return

        # Основная статистика
        self.communicator.say("\nРезультаты фундаментального анализа:")
        self.communicator.say(f"- Проанализировано новостей: {results.get('total_articles', 0)}")

        # Результаты NLP-анализа тональности
        sentiment_analysis = results.get('sentiment_analysis', {})
        if sentiment_analysis and sentiment_analysis != 'no_data':
            self.communicator.say("\nNLP-анализ тональности:")
            self.communicator.say(f"- Положительных новостей: {sentiment_analysis.get('positive_count', 0)} " +
                                f"({sentiment_analysis.get('positive_ratio', 0):.1%})")
            self.communicator.say(f"- Отрицательных новостей: {sentiment_analysis.get('negative_count', 0)} " +
                                f"({sentiment_analysis.get('negative_ratio', 0):.1%})")
            self.communicator.say(f"- Общая тональность: {sentiment_analysis.get('overall_sentiment', 'нейтральная')}")

        # Важные новости с их тональностью
        important_news = results.get('important_news', [])
        if important_news:
            self.communicator.say("\nВажные новости и их тональность:")
            for news in important_news[:5]:
                # Находим тональность для этой новости
                sentiment = "нейтральная"
                sentiments = sentiment_analysis.get('sentiments', [])
                if news and sentiments:
                    for s in sentiments:
                        if s.get('title') == news.get('title'):
                            sentiment = "положительная" if s.get('label') == 'POSITIVE' else "отрицательная"
                            break

                self.communicator.say(f"- {news.get('title', 'Без заголовка')} ({news.get('source', 'Н/Д')}) - {sentiment}")

    def _display_technical_results(self, results: Dict[str, Any]):
        """Отображение результатов технического анализа"""
        if results.get('status') != 'success':
            self.communicator.show_warning("Ошибка при выполнении технического анализа")
            return

        analysis = results.get('analysis', {})
        indicators = results.get('indicators', {})

        self.communicator.say("\nРезультаты технического анализа:")
        self.communicator.say(f"- Текущая цена: ${indicators['last_close']:.2f}")
        self.communicator.say(f"- Текущий тренд: {analysis['trend']}")
        self.communicator.say(f"- RSI: {indicators['last_rsi']:.2f} ({analysis['signals']['RSI']})")
        self.communicator.say(f"- MACD: {analysis['signals']['MACD']}")

        # Уровни поддержки и сопротивления
        if analysis['support_levels']:
            support_str = ", ".join([f"${level:.2f}" for level in analysis['support_levels']])
            self.communicator.say(f"- Уровни поддержки: {support_str}")

        if analysis['resistance_levels']:
            resistance_str = ", ".join([f"${level:.2f}" for level in analysis['resistance_levels']])
            self.communicator.say(f"- Уровни сопротивления: {resistance_str}")

        self.communicator.say(f"- Общий технический сигнал: {analysis['overall_signal']}")

    def _display_risk_results(self, results: Dict[str, Any]):
        """Отображение результатов риск-менеджмента"""
        if results.get('status') != 'success':
            self.communicator.show_warning("Ошибка при выполнении анализа рисков")
            return

        risk_metrics = results.get('risk_metrics', {})
        assessment = results.get('risk_assessment', {})

        self.communicator.say("\nРезультаты анализа рисков:")
        self.communicator.say(f"- VaR (95%): {risk_metrics.get('var_95', 0):.2f}% (вероятный максимальный убыток)")
        self.communicator.say(f"- VaR (5 дней): {risk_metrics.get('var_5d_95', 0):.2f}%")
        self.communicator.say(f"- VaR (10 дней): {risk_metrics.get('var_10d_95', 0):.2f}%")
        self.communicator.say(f"- Волатильность: {risk_metrics.get('volatility', 0):.2f}%")
        self.communicator.say(f"- Коэффициент Шарпа: {risk_metrics.get('sharpe_ratio', 0):.2f}")

        # Пример потенциальных потерь
        investment = risk_metrics.get('investment_example', 10000)
        loss = risk_metrics.get('potential_loss_95', 0)
        self.communicator.say(f"- Потенциальные потери от ${investment:.2f}: ${loss:.2f} (с вероятностью 95%)")

        # Добавляем информацию об оптимизации позиции
        self.communicator.say("\nОптимизация позиции:")

        # Рекомендации по стоп-лоссу
        stop_loss = risk_metrics.get('stop_loss', {}).get('moderate', {})
        if stop_loss:
            sl_percent = stop_loss.get('percent', 0)
            sl_price = stop_loss.get('price_level', 0)
            self.communicator.say(f"- Рекомендуемый стоп-лосс: {sl_percent:.2f}% (${sl_price:.2f})")

        # Рекомендуемый размер позиции
        position = risk_metrics.get('position_sizing', {}).get('moderate', {})
        if position:
            pos_percent = position.get('capital_percent', 0)
            pos_value = position.get('position_value', 0)
            self.communicator.say(f"- Рекомендуемый размер позиции: {pos_percent:.2f}% от капитала (${pos_value:.2f})")
            self.communicator.say(f"- Потенциальные потери при срабатывании стоп-лосса: ${position.get('potential_loss', 0):.2f}")
            self.communicator.say(f"- Рекомендуемое соотношение риск/прибыль: 1:{position.get('risk_reward_ratio', 2.0)}")

        # Оценка риска
        self.communicator.say(f"\nОценка рисков: {assessment.get('summary', 'Н/Д')}")

        # Рекомендация
        if 'recommendation' in assessment:
            self.communicator.say(f"\nРекомендация по управлению рисками: {assessment['recommendation']}")

    def _make_final_conclusion(self, block_trades: Dict[str, Any], fundamental: Dict[str, Any],
                         technical: Dict[str, Any], risk: Dict[str, Any] = None):
        """Формирование итогового заключения"""
        self.communicator.say("\nИтоговое заключение:")

        # Технический анализ
        technical_sentiment = technical['analysis']['overall_signal'] if technical['status'] == 'success' else "нейтральный"
        self.communicator.say(f"- Технический анализ: {technical_sentiment}")

        # Анализ блочных сделок
        option_sentiment = "бычье" if block_trades['total_delta'] > 100 else "медвежье" if block_trades['total_delta'] < -100 else "нейтральное"
        self.communicator.say(f"- Анализ опционов: {option_sentiment}")

        # Фундаментальный анализ
        news_sentiment = fundamental.get('sentiment', 'neutral')
        self.communicator.say(f"- Анализ новостей: {news_sentiment}")

        # Определение общего сигнала
        sentiments = [technical_sentiment, option_sentiment, news_sentiment]
        bull_count = sum(1 for s in sentiments if "быч" in s or "восходящ" in s)
        bear_count = sum(1 for s in sentiments if "медвеж" in s or "нисходящ" in s)

        if risk and risk.get('status') == 'success':
            risk_level = risk.get('risk_assessment', {}).get('risk_level', 'не определен')
            self.communicator.say(f"- Уровень риска: {risk_level}")

            # Учитываем риск в рекомендации
            if risk_level == "высокий":
                self.communicator.say("(!) Внимание: высокий уровень риска требует дополнительных мер защиты")

        if bull_count >= 2:
            self.communicator.say("Рекомендация: ПОКУПАТЬ - большинство индикаторов указывают на рост")
        elif bear_count >= 2:
            self.communicator.say("Рекомендация: ПРОДАВАТЬ - большинство индикаторов указывают на снижение")
        else:
            self.communicator.say("Рекомендация: ДЕРЖАТЬ - сигналы смешанные, требуется дополнительный анализ")

    def _display_recommendations(self, results: Dict[str, Any]):
        """Отображение итоговых рекомендаций"""
        if results.get('status') != 'success':
            self.communicator.show_warning("Ошибка при формировании рекомендаций")
            return

        recommendations = results.get('recommendations', {})
        report_path = results.get('report_path', '')

        self.communicator.say("\nИтоговые рекомендации:")
        self.communicator.say(f"- Рекомендуемое действие: {recommendations.get('recommendation', 'Н/Д')}")
        self.communicator.say(f"- Уровень риска: {recommendations.get('risk_level', 'Н/Д')}")

        # Вывод стратегии входа и управления рисками
        self.communicator.say("\nСтратегия входа:")
        self.communicator.say(f"- {recommendations.get('entry_strategy', 'Н/Д')}")

        self.communicator.say("\nУправление позицией:")
        self.communicator.say(f"- Размер позиции: {recommendations.get('position_size', 0)}% от капитала")
        self.communicator.say(f"- Стоп-лосс: ${recommendations.get('stop_loss_price', 0)} ({recommendations.get('stop_loss_percent', 0)}%)")
        self.communicator.say(f"- Тейк-профит: ${recommendations.get('take_profit_price', 0)} ({recommendations.get('take_profit_percent', 0)}%)")
        self.communicator.say(f"- Соотношение риск/прибыль: 1:{recommendations.get('risk_reward_ratio', 0)}")

        # Вывод информации о сгенерированном отчете
        if report_path:
            self.communicator.say(f"\nСгенерирован LaTeX-отчет: {report_path}")
            self.communicator.say("Для компиляции в PDF используйте команду pdflatex.")

    def process_trades_for_telegram(self, currency: str, days: int) -> Dict[str, Any]:
        """
        Обработка торговых данных для Telegram-бота

        Args:
            currency: Валюта для анализа
            days: Количество дней для анализа

        Returns:
            Dict[str, Any]: Результаты анализа
        """
        try:
            # Сохраняем параметры в память
            self.memory.update_context({
                'currency': currency,
                'days': days,
                'timestamp': datetime.now()
            })

            # Этап 1: Анализ блочных сделок
            self.state = AgentState.BLOCK_TRADES_ANALYSIS
            block_trades_results = self.block_trades_analyzer.analyze(currency, days) or {}
            self.memory.update_context({'block_trades_analysis': block_trades_results})

            # Этап 2: Фундаментальный анализ
            self.state = AgentState.FUNDAMENTAL_ANALYSIS
            fundamental_results = self.fundamental_analyzer.analyze(currency, days) or {}
            self.memory.update_context({'fundamental_analysis': fundamental_results})

            # Этап 3: Технический анализ
            self.state = AgentState.TECHNICAL_ANALYSIS
            technical_results = self.technical_analyzer.analyze(currency, days) or {}
            self.memory.update_context({'technical_analysis': technical_results})

            # Этап 4: Риск-менеджмент
            self.state = AgentState.RISK_MANAGEMENT
            risk_results = self.risk_management_analyzer.analyze(currency, days) or {}
            self.memory.update_context({'risk_management': risk_results})

            # Этап 5: Формирование рекомендаций и отчета
            self.state = AgentState.RECOMMENDATIONS
            recommendations_results = self.recommendation_generator.generate(currency, days) or {}
            self.memory.update_context({'recommendations': recommendations_results})

            return recommendations_results

        except Exception as e:
            logger.error(f"Ошибка при обработке данных для Telegram: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
