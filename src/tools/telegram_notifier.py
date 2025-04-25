# src/tools/telegram_notifier.py

import asyncio
import logging
from typing import Dict, Any, List, Optional
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Класс для отправки уведомлений в Telegram"""

    def __init__(self, token: str, chat_ids: List[str]):
        """
        Инициализация нотификатора

        Args:
            token (str): Токен Telegram бота
            chat_ids (List[str]): Список ID чатов для отправки уведомлений
        """
        self.token = token
        self.chat_ids = chat_ids
        self.bot = Bot(token=token)

    async def _send_message_async(self, chat_id, text, parse_mode=None):
        """Асинхронная отправка сообщения"""
        try:
            await self.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            return False

    def send_message(self, message: str, parse_mode=None) -> bool:
        """
        Отправляет текстовое сообщение

        Args:
            message (str): Текст сообщения
            parse_mode: Режим парсинга текста

        Returns:
            bool: True если отправка успешна, иначе False
        """
        if parse_mode is None:
            parse_mode = ParseMode.HTML

        try:
            # Обновляем на использование event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            for chat_id in self.chat_ids:
                loop.run_until_complete(self._send_message_async(chat_id, message, parse_mode))

            loop.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в Telegram: {e}")
            return False

    def send_analysis_report(self, analysis_data: Dict[str, Any]) -> bool:
        """
        Отправляет форматированный отчет с результатами анализа

        Args:
            analysis_data (Dict[str, Any]): Данные анализа

        Returns:
            bool: True если отправка успешна, иначе False
        """
        try:
            # Формируем отчет в HTML формате
            currency = analysis_data.get('currency', 'Криптовалюта')
            current_price = analysis_data.get('current_price', '0')
            recommendation = analysis_data.get('recommendation', 'Н/Д')
            risk_level = analysis_data.get('risk_level', 'Н/Д')

            # Заголовок отчета
            report = f"<b>🔍 ОПЦИОННЫЙ АНАЛИЗ: {currency} ${current_price}</b>\n\n"

            # ======= БЛОК ОПЦИОНОВ (РАСШИРЕННЫЙ) =======
            report += "<b>🔄 АНАЛИЗ ОПЦИОНОВ И БЛОЧНЫХ СДЕЛОК:</b>\n"

            # Общая статистика опционов
            calls_count = analysis_data.get('calls_count', 'Н/Д')
            puts_count = analysis_data.get('puts_count', 'Н/Д')
            call_volume = analysis_data.get('call_volume', 'Н/Д')
            put_volume = analysis_data.get('put_volume', 'Н/Д')
            call_put_ratio = analysis_data.get('call_put_ratio', 'Н/Д')

            report += f"• Всего сделок: <b>{analysis_data.get('total_trades', 'Н/Д')}</b>\n"
            report += f"• CALL опционов: <b>{calls_count}</b> (объем {call_volume})\n"
            report += f"• PUT опционов: <b>{puts_count}</b> (объем {put_volume})\n"
            report += f"• Соотношение CALL/PUT: <b>{call_put_ratio}</b>\n"
            report += f"• Общая дельта: <b>{analysis_data.get('total_delta', 'Н/Д')}</b> 🔑\n\n"

            # Распределение стратегий - ключевая часть
            report += "<b>📊 РАСПРЕДЕЛЕНИЕ ОПЦИОННЫХ СТРАТЕГИЙ:</b>\n"
            strategies_data = analysis_data.get('strategies_data', {})
            if strategies_data:
                for strategy, volume in sorted(strategies_data.items(), key=lambda x: x[1], reverse=True)[:5]:
                    total_volume = sum(strategies_data.values())
                    percentage = (volume/total_volume*100) if total_volume > 0 else 0
                    report += f"• <b>{strategy}</b>: {volume:.2f} ({percentage:.1f}%)\n"
            else:
                report += "• Данные о стратегиях недоступны\n"

            # Крупнейшие сделки - новый раздел
            report += "\n<b>💼 КРУПНЕЙШИЕ СДЕЛКИ:</b>\n"
            largest_trades = analysis_data.get('largest_trades', [])
            if largest_trades:
                for i, trade in enumerate(largest_trades[:5], 1):
                    trade_type = trade.get('type', 'Неизвестно')
                    trade_amount = trade.get('amount', 0)
                    trade_id = trade.get('trade_id', 'Н/Д')
                    report += f"• #{i}: <b>{trade_type}</b> - объем {trade_amount:.2f} (ID: {trade_id})\n"
            else:
                report += "• Данные о крупных сделках недоступны\n"

            # Основной сигнал от опционов
            option_sentiment = analysis_data.get('option_sentiment', 'нейтральное')
            report += f"\n<b>📣 СИГНАЛ ПО ОПЦИОНАМ:</b> <u>{option_sentiment}</u>\n\n"

            # ======= КЛЮЧЕВАЯ РЕКОМЕНДАЦИЯ =======
            report += f"<b>🎯 ОБЩАЯ РЕКОМЕНДАЦИЯ: {recommendation}</b>\n"
            report += f"<b>⚠️ Уровень риска:</b> {risk_level}\n\n"

            # ======= ТЕХНИЧЕСКИЙ АНАЛИЗ (СОКРАЩЕННЫЙ) =======
            report += "<b>📈 Технический анализ:</b>\n"
            report += f"• Тренд: {analysis_data.get('trend', 'Н/Д')}\n"
            report += f"• RSI: {analysis_data.get('rsi_value', 'Н/Д')} ({analysis_data.get('rsi_signal', 'Н/Д')})\n"
            report += f"• Сигнал: {analysis_data.get('technical_signal', 'Н/Д')}\n\n"

            # ======= РИСК-МЕНЕДЖМЕНТ (СОКРАЩЕННЫЙ) =======
            report += "<b>🛡️ Риск-менеджмент:</b>\n"
            report += f"• Размер позиции: {analysis_data.get('position_size', 'Н/Д')}% капитала\n"
            report += f"• Стоп-лосс: ${analysis_data.get('stop_loss_price', 'Н/Д')} ({analysis_data.get('stop_loss_percent', 'Н/Д')}%)\n"
            report += f"• Тейк-профит: ${analysis_data.get('take_profit_price', 'Н/Д')} ({analysis_data.get('take_profit_percent', 'Н/Д')}%)\n"

            # Отправляем основной отчет
            success = self.send_message(report, ParseMode.HTML)
            if not success:
                return False

            # Отправляем заключение отдельным сообщением для лучшей читаемости
            conclusion = analysis_data.get('conclusion', '')
            if conclusion:
                conclusion_msg = "<b>📝 ЗАКЛЮЧЕНИЕ И ПРОГНОЗ:</b>\n\n" + conclusion
                # Обрезаем сообщение, если оно слишком длинное
                if len(conclusion_msg) > 4000:
                    conclusion_msg = conclusion_msg[:3997] + "..."

                return self.send_message(conclusion_msg, ParseMode.HTML)

            return True
        except Exception as e:
            logger.error(f"Ошибка отправки отчета в Telegram: {e}")
            return False
