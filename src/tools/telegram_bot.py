# src/tools/telegram_bot.py

import logging
import threading
from typing import Dict, Any, List, Optional, Callable
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import asyncio

logger = logging.getLogger(__name__)

# Состояния для обработки разговора
CHOOSING_CURRENCY, CHOOSING_DAYS, PROCESSING = range(3)

class TelegramBot:
    """Интерактивный Telegram бот для торгового агента"""
    
    def __init__(self, token: str, allowed_user_ids: List[int] = None):
        """
        Инициализация бота
        
        Args:
            token (str): Токен Telegram бота
            allowed_user_ids (List[int], optional): Список ID пользователей, которым разрешено использовать бота
        """
        self.token = token
        self.allowed_user_ids = allowed_user_ids or []
        self.is_running = False
        self.agent = None  # Ссылка на торгового агента, будет установлена позже
        
        # Создаем приложение бота
        self.application = Application.builder().token(token).build()
        
        # Регистрируем обработчики
        self._register_handlers()
    
    def set_agent(self, agent):
        """Устанавливает ссылку на торгового агента"""
        self.agent = agent
    
    def _register_handlers(self):
        """Регистрация обработчиков команд и сообщений"""
        # Основные команды
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("analyze", self._analyze_command))
        self.application.add_handler(CommandHandler("status", self._status_command))
        self.application.add_handler(CommandHandler("settings", self._settings_command))
        
        # Обработчики разговоров для анализа
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("analyze", self._analyze_command)],
            states={
                CHOOSING_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_currency)],
                CHOOSING_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_days)],
            },
            fallbacks=[CommandHandler("cancel", self._cancel_command)],
        )
        self.application.add_handler(conv_handler)
        
        # Обработчик callback кнопок
        self.application.add_handler(CallbackQueryHandler(self._button_callback))
        
        # Обработчик обычных сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Обработчик ошибок
        self.application.add_error_handler(self._error_handler)
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user_id = update.effective_user.id
        
        # Проверка авторизации, если указан список разрешенных пользователей
        if self.allowed_user_ids and user_id not in self.allowed_user_ids:
            await update.message.reply_text("⛔ Извините, у вас нет доступа к этому боту.")
            return
        
        # Приветственное сообщение
        welcome_text = (
            f"👋 <b>Здравствуйте, {update.effective_user.first_name}!</b>\n\n"
            "Я торговый агент с аналитикой опционного рынка криптовалют.\n\n"
            "📊 <b>Мои возможности:</b>\n"
            "• Анализ опционных сделок\n"
            "• Технический анализ\n"
            "• Фундаментальный анализ\n"
            "• Оценка рисков и рекомендации\n\n"
            "Используйте /analyze для начала нового анализа или /help для справки."
        )
        
        # Создаем клавиатуру с основными действиями
        keyboard = [
            [InlineKeyboardButton("📊 Новый анализ", callback_data="new_analysis")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        help_text = (
            "<b>📖 Справка по командам:</b>\n\n"
            "/analyze - Запустить новый анализ\n"
            "/status - Узнать статус текущего анализа\n"
            "/settings - Настройки параметров анализа\n"
            "/help - Показать эту справку\n\n"
            "<b>Как пользоваться:</b>\n"
            "1. Запустите команду /analyze\n"
            "2. Выберите валюту для анализа (BTC или ETH)\n"
            "3. Укажите количество дней для анализа (14-365)\n"
            "4. Дождитесь результатов анализа\n\n"
            "<b>Вопросы по анализу:</b>\n"
            "Вы можете задать вопросы по полученной аналитике, например:\n"
            "- \"Подробнее об опционных стратегиях\"\n"
            "- \"Объясни сигнал RSI\"\n"
            "- \"Что означает перевес CALL опционов?\""
        )
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
    
    async def _analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запуск процесса анализа"""
        # Проверка авторизации
        user_id = update.effective_user.id
        if self.allowed_user_ids and user_id not in self.allowed_user_ids:
            await update.message.reply_text("⛔ Извините, у вас нет доступа к этому боту.")
            return ConversationHandler.END
        
        # Создаем клавиатуру для выбора валюты
        keyboard = [
            [
                InlineKeyboardButton("Bitcoin (BTC)", callback_data="currency_BTC"),
                InlineKeyboardButton("Ethereum (ETH)", callback_data="currency_ETH")
            ],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🪙 <b>Выберите валюту для анализа:</b>", 
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return CHOOSING_CURRENCY
    
    async def _handle_currency(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора валюты"""
        currency = update.message.text.upper()
        
        if currency not in ['BTC', 'ETH']:
            await update.message.reply_text(
                "❌ Неподдерживаемая валюта. Пожалуйста, введите BTC или ETH."
            )
            return CHOOSING_CURRENCY
        
        # Сохраняем валюту в контексте
        context.user_data['currency'] = currency
        
        # Создаем клавиатуру для выбора периода
        keyboard = [
            [
                InlineKeyboardButton("14 дней", callback_data="days_14"),
                InlineKeyboardButton("30 дней", callback_data="days_30")
            ],
            [
                InlineKeyboardButton("60 дней", callback_data="days_60"),
                InlineKeyboardButton("90 дней", callback_data="days_90")
            ],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📅 <b>Выберите период для анализа (14-365 дней):</b>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return CHOOSING_DAYS
    
    async def _handle_days(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора количества дней"""
        try:
            days = int(update.message.text)
            
            if not 14 <= days <= 365:
                await update.message.reply_text(
                    "❌ Количество дней должно быть от 14 до 365. Попробуйте снова."
                )
                return CHOOSING_DAYS
                
            # Сохраняем количество дней в контексте
            context.user_data['days'] = days
            
            # Запускаем анализ
            await self._start_analysis(update, context)
            
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ Пожалуйста, введите число от 14 до 365."
            )
            return CHOOSING_DAYS
    
    async def _start_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запуск процесса анализа"""
        currency = context.user_data.get('currency')
        days = context.user_data.get('days')
        
        if not currency or not days:
            await update.message.reply_text("❌ Ошибка: не указаны параметры анализа.")
            return
        
        await update.message.reply_text(
            f"🔄 <b>Начинаю анализ {currency} за последние {days} дней...</b>\n\n"
            "Это может занять некоторое время. Вы получите уведомление, когда анализ будет завершен.",
            parse_mode=ParseMode.HTML
        )
        
        # Запускаем анализ в отдельном потоке, чтобы не блокировать бота
        threading.Thread(
            target=self._run_analysis_thread,
            args=(update.effective_chat.id, currency, days)
        ).start()
    
    def _run_analysis_thread(self, chat_id, currency, days):
        """Выполнение анализа в отдельном потоке"""
        try:
            if not self.agent:
                self._send_message(chat_id, "❌ Ошибка: агент не инициализирован.")
                return
                    
            # Вызываем метод анализа из агента
            results = self.agent.process_trades_for_telegram(currency, days)
            
            # Отправляем результаты анализа
            if results and results.get('status') == 'success':
                self._send_message(
                    chat_id, 
                    "✅ <b>Анализ успешно завершен!</b>\n\nОтправляю результаты...",
                    parse_mode=ParseMode.HTML
                )
                
                # Отправляем отчет
                self._send_analysis_report(chat_id, results.get('recommendations', {}))
                
                # Добавим подсказку о возможности задать вопросы
                self._send_message(
                    chat_id,
                    "👆 <b>Теперь вы можете задать дополнительные вопросы по анализу:</b>\n\n"
                    "• Что означает такое значение RSI?\n"
                    "• Какие основные опционные стратегии используются?\n"
                    "• Почему рекомендуется именно этот стоп-лосс?\n"
                    "• Как интерпретировать соотношение CALL/PUT?\n\n"
                    "Локальная модель Llama обработает ваш вопрос и предоставит ответ на основе проведенного анализа.",
                    parse_mode=ParseMode.HTML
                )
            else:
                self._send_message(
                    chat_id, 
                    "❌ Ошибка при выполнении анализа. Пожалуйста, попробуйте позже."
                )
        except Exception as e:
            logger.error(f"Ошибка в потоке анализа: {e}")
            self._send_message(
                chat_id, 
                f"❌ Произошла ошибка при анализе: {str(e)}"
            )
    
    async def _cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена текущей операции"""
        context.user_data.clear()
        await update.message.reply_text(
            "✅ Операция отменена. Используйте /analyze для начала нового анализа."
        )
        return ConversationHandler.END
    
    async def _button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        if callback_data == "new_analysis":
            # Перенаправляем на команду analyze
            await self._analyze_command(update, context)
            
        elif callback_data == "help":
            # Показываем справку
            await query.edit_message_text(text="Переход к справке...")
            await self._help_command(update, context)
            
        elif callback_data == "cancel":
            # Отменяем текущую операцию
            context.user_data.clear()
            await query.edit_message_text(
                text="✅ Операция отменена. Используйте /analyze для начала нового анализа."
            )
            return ConversationHandler.END
            
        elif callback_data.startswith("currency_"):
            # Обработка выбора валюты через кнопку
            currency = callback_data.split("_")[1]
            context.user_data['currency'] = currency
            
            # Создаем клавиатуру для выбора периода
            keyboard = [
                [
                    InlineKeyboardButton("14 дней", callback_data="days_14"),
                    InlineKeyboardButton("30 дней", callback_data="days_30")
                ],
                [
                    InlineKeyboardButton("60 дней", callback_data="days_60"),
                    InlineKeyboardButton("90 дней", callback_data="days_90")
                ],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=f"Выбрана валюта: {currency}\n\n📅 <b>Выберите период для анализа:</b>",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
            return CHOOSING_DAYS
            
        elif callback_data.startswith("days_"):
            # Обработка выбора дней через кнопку
            days = int(callback_data.split("_")[1])
            context.user_data['days'] = days
            
            # Запускаем анализ
            await query.edit_message_text(
                text=f"🔄 <b>Начинаю анализ {context.user_data.get('currency')} за последние {days} дней...</b>\n\n"
                "Это может занять некоторое время. Вы получите уведомление, когда анализ будет завершен.",
                parse_mode=ParseMode.HTML
            )
            
            # Запускаем анализ в отдельном потоке
            threading.Thread(
                target=self._run_analysis_thread,
                args=(update.effective_chat.id, context.user_data.get('currency'), days)
            ).start()
            
            return ConversationHandler.END
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Информация о статусе агента"""
        if not self.agent:
            await update.message.reply_text("❌ Агент не инициализирован.")
            return
            
        state = self.agent.state
        
        status_text = (
            f"<b>📊 Статус агента:</b>\n\n"
            f"• Текущее состояние: {state}\n"
        )
        
        # Добавляем информацию о последнем анализе, если есть
        memory = self.agent.memory.get_context()
        if memory:
            currency = memory.get('currency')
            days = memory.get('days')
            timestamp = memory.get('timestamp')
            
            if currency and days and timestamp:
                status_text += (
                    f"\n<b>Последний анализ:</b>\n"
                    f"• Валюта: {currency}\n"
                    f"• Период: {days} дней\n"
                    f"• Время выполнения: {timestamp}\n"
                )
        
        await update.message.reply_text(status_text, parse_mode=ParseMode.HTML)
    
    async def _settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Настройки пользователя"""
        settings_text = (
            "<b>⚙️ Настройки агента:</b>\n\n"
            "Здесь вы можете настроить параметры анализа:"
        )
        
        # Создаем клавиатуру с настройками
        keyboard = [
            [InlineKeyboardButton("🔍 Уровень детализации", callback_data="settings_detail")],
            [InlineKeyboardButton("⚠️ Порог риска", callback_data="settings_risk")],
            [InlineKeyboardButton("🔔 Уведомления", callback_data="settings_notifications")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            settings_text, 
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка обычных текстовых сообщений и вопросов"""
        message_text = update.message.text.lower()
        
        # Простая система ответов на вопросы для базовых тем
        if "опционн" in message_text and "стратег" in message_text:
            await self._explain_option_strategies(update, context)
        elif "call" in message_text and ("перевес" in message_text or "превыша" in message_text):
            await self._explain_call_dominance(update, context)
        elif "rsi" in message_text:
            await self._explain_rsi(update, context)
        elif "риск" in message_text:
            await self._explain_risk(update, context)
        else:
            # Получаем последние данные анализа из контекста
            analysis_data = {}
            if self.agent:
                memory = self.agent.memory.get_context()
                if 'recommendations' in memory and 'recommendations' in memory['recommendations']:
                    analysis_data = memory['recommendations']['recommendations']
            
            # Если нет данных анализа, сообщаем пользователю
            if not analysis_data:
                await update.message.reply_text(
                    "🤔 Я не совсем понял ваш вопрос, и у меня нет данных последнего анализа. "
                    "Пожалуйста, сначала выполните анализ с помощью команды /analyze."
                )
                return
            
            # Отправляем индикатор печати, чтобы показать, что обрабатываем вопрос
            await update.message.chat.send_action(action="typing")
            
            # Получаем ответ от Ollama в отдельном потоке
            def get_ollama_answer():
                return self.agent.tools.ask_ollama(update.message.text, analysis_data)
            
            # Запускаем в отдельном потоке, чтобы не блокировать бота
            loop = asyncio.get_event_loop()
            answer = await loop.run_in_executor(None, get_ollama_answer)
            
            # Отправляем ответ
            await update.message.reply_text(answer)

    async def _explain_option_strategies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Объяснение опционных стратегий"""
        strategies_text = (
            "<b>📚 Основные опционные стратегии:</b>\n\n"
            "• <b>Single Trade</b> - Простая покупка/продажа одного опциона. Отражает прямую ставку на направление движения цены.\n\n"
            "• <b>Call Spread</b> - Покупка и продажа CALL опционов с разными страйками. Ограничивает риск и прибыль, используется при умеренно бычьем настрое.\n\n"
            "• <b>Put Spread</b> - Покупка и продажа PUT опционов с разными страйками. Ограничивает риск и прибыль, используется при умеренно медвежьем настрое.\n\n"
            "• <b>Risk Reversal</b> - Комбинация продажи PUT и покупки CALL (или наоборот). Отражает сильную направленную ставку.\n\n"
            "• <b>Straddle</b> - Одновременная покупка CALL и PUT опционов с одинаковым страйком. Ставка на волатильность без уверенности в направлении.\n\n"
            "• <b>Iron Condor</b> - Комбинация спредов. Прибыльна при движении цены в определённом диапазоне.\n\n"
            "<b>Интерпретация:</b> Преобладание определенных стратегий указывает на настроение крупных игроков. Например, большой объем Call Spread говорит об умеренно бычьих ожиданиях."
        )
        
        await update.message.reply_text(strategies_text, parse_mode=ParseMode.HTML)
    
    async def _explain_call_dominance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Объяснение преобладания CALL опционов"""
        call_text = (
            "<b>📈 Преобладание CALL опционов:</b>\n\n"
            "Когда объем CALL опционов значительно превышает объем PUT, это обычно указывает на <b>бычье настроение</b> рынка.\n\n"
            "<b>Что это значит:</b>\n"
            "• Трейдеры ожидают роста цены актива\n"
            "• Покупатели CALL опционов готовы платить премию за возможность купить актив по заранее оговоренной цене\n"
            "• Высокий CALL/PUT ratio (>1.5) часто сигнализирует о избыточном оптимизме\n\n"
            "<b>Контекст важен:</b> Необходимо анализировать также дельту позиций, распределение страйков и сроки экспирации для полной картины."
        )
        
        await update.message.reply_text(call_text, parse_mode=ParseMode.HTML)
    
    async def _explain_rsi(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Объяснение индикатора RSI"""
        rsi_text = (
            "<b>📊 Индекс относительной силы (RSI):</b>\n\n"
            "RSI - технический индикатор, измеряющий скорость и изменение ценовых движений. Диапазон значений от 0 до 100.\n\n"
            "<b>Интерпретация:</b>\n"
            "• <b>RSI > 70</b>: актив считается перекупленным (возможна коррекция вниз)\n"
            "• <b>RSI < 30</b>: актив считается перепроданным (возможен отскок вверх)\n"
            "• <b>RSI = 50</b>: нейтральное положение\n\n"
            "<b>Сигналы:</b>\n"
            "• Дивергенции между RSI и ценой\n"
            "• Пробой уровня центральной линии (50)\n"
            "• Формирование паттернов на самом RSI\n\n"
            "Важно анализировать RSI в контексте других индикаторов и общего тренда рынка."
        )
        
        await update.message.reply_text(rsi_text, parse_mode=ParseMode.HTML)
    
    async def _explain_risk(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Объяснение оценки рисков"""
        risk_text = (
            "<b>⚠️ Оценка риска и VaR:</b>\n\n"
            "Value at Risk (VaR) - статистическая метрика, оценивающая максимально возможные потери за определенный период с заданной вероятностью.\n\n"
            "<b>Как интерпретировать:</b>\n"
            "• <b>VaR 95%</b>: с вероятностью 95% ваши потери не превысят этого значения\n"
            "• <b>Высокий VaR</b>: указывает на повышенный риск и волатильность\n"
            "• <b>Низкий VaR</b>: указывает на более стабильный актив\n\n"
            "<b>Управление позицией:</b>\n"
            "• Размер позиции рассчитывается с учетом вашего капитала и допустимого риска\n"
            "• Стоп-лосс устанавливается на основе волатильности актива\n"
            "• Соотношение риск/прибыль (R/R) должно быть не менее 1:2 для благоприятной торговли\n\n"
            "Помните: никакой анализ не даёт 100% гарантии, всегда рискуйте только тем, что готовы потерять."
        )
        
        await update.message.reply_text(risk_text, parse_mode=ParseMode.HTML)
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Ошибка при обработке запроса: {context.error}")
    
    def _send_message(self, chat_id, text, parse_mode=None):
        """Синхронный метод для отправки сообщения из потока"""
        if parse_mode is None:
            parse_mode = ParseMode.HTML
            
        asyncio.run(self._send_message_async(chat_id, text, parse_mode))
    
    async def _send_message_async(self, chat_id, text, parse_mode=None):
        """Асинхронная отправка сообщения"""
        bot = Bot(token=self.token)
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
    
    def _send_analysis_report(self, chat_id, analysis_data):
        """Отправка результатов анализа"""
        try:
            # Формируем отчет в HTML формате (как и раньше)
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
            
            # Отправляем первую часть отчета
            self._send_message(chat_id, report)
            
            # Создаем и отправляем вторую часть - стратегии
            report2 = "<b>📊 РАСПРЕДЕЛЕНИЕ ОПЦИОННЫХ СТРАТЕГИЙ:</b>\n"
            strategies_data = analysis_data.get('strategies_data', {})
            if strategies_data:
                total_volume = sum(strategies_data.values())
                for strategy, volume in sorted(strategies_data.items(), key=lambda x: x[1], reverse=True)[:5]:
                    percentage = (volume/total_volume*100) if total_volume > 0 else 0
                    report2 += f"• <b>{strategy}</b>: {volume:.2f} ({percentage:.1f}%)\n"
            else:
                report2 += "• Данные о стратегиях недоступны\n"
                
            # Крупнейшие сделки
            report2 += "\n<b>💼 КРУПНЕЙШИЕ СДЕЛКИ:</b>\n"
            largest_trades = analysis_data.get('largest_trades', [])
            if largest_trades:
                for i, trade in enumerate(largest_trades[:5], 1):
                    trade_type = trade.get('type', 'Неизвестно')
                    trade_amount = trade.get('amount', 0)
                    trade_id = trade.get('trade_id', 'Н/Д')
                    report2 += f"• #{i}: <b>{trade_type}</b> - объем {trade_amount:.2f} (ID: {trade_id})\n"
            else:
                report2 += "• Данные о крупных сделках недоступны\n"
            
            # Основной сигнал от опционов
            option_sentiment = analysis_data.get('option_sentiment', 'нейтральное')
            report2 += f"\n<b>📣 СИГНАЛ ПО ОПЦИОНАМ:</b> <u>{option_sentiment}</u>\n"
            
            # Отправляем вторую часть
            self._send_message(chat_id, report2)
            
            # Создаем и отправляем третью часть - общая рекомендация
            report3 = f"<b>🎯 ОБЩАЯ РЕКОМЕНДАЦИЯ: {recommendation}</b>\n"
            report3 += f"<b>⚠️ Уровень риска:</b> {risk_level}\n\n"
            
            # Технический анализ
            report3 += "<b>📈 Технический анализ:</b>\n"
            report3 += f"• Тренд: {analysis_data.get('trend', 'Н/Д')}\n"
            report3 += f"• RSI: {analysis_data.get('rsi_value', 'Н/Д')} ({analysis_data.get('rsi_signal', 'Н/Д')})\n"
            report3 += f"• Сигнал: {analysis_data.get('technical_signal', 'Н/Д')}\n\n"
            
            # Риск-менеджмент
            report3 += "<b>🛡️ Риск-менеджмент:</b>\n"
            report3 += f"• Размер позиции: {analysis_data.get('position_size', 'Н/Д')}% капитала\n"
            report3 += f"• Стоп-лосс: ${analysis_data.get('stop_loss_price', 'Н/Д')} ({analysis_data.get('stop_loss_percent', 'Н/Д')}%)\n"
            report3 += f"• Тейк-профит: ${analysis_data.get('take_profit_price', 'Н/Д')} ({analysis_data.get('take_profit_percent', 'Н/Д')}%)\n"
            
            # Отправляем третью часть
            self._send_message(chat_id, report3)
            
            # Отправляем заключение отдельным сообщением
            conclusion = analysis_data.get('conclusion', '')
            if conclusion:
                conclusion_msg = "<b>📝 ЗАКЛЮЧЕНИЕ И ПРОГНОЗ:</b>\n\n" + conclusion
                # Обрезаем сообщение, если оно слишком длинное
                if len(conclusion_msg) > 4000:
                    conclusion_msg = conclusion_msg[:3997] + "..."
                
                self._send_message(chat_id, conclusion_msg)
            
            # Отправляем сообщение с предложением задать вопросы
            self._send_message(
                chat_id,
                "👆 <b>Теперь вы можете задать дополнительные вопросы по анализу.</b>\n\n"
                "Например:\n"
                "• Подробнее об опционных стратегиях\n"
                "• Что означает перевес CALL опционов?\n"
                "• Объясни сигнал RSI\n"
                "• Что означает этот уровень риска?\n\n"
                "Используйте /analyze для нового анализа."
            )
            
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки отчета: {e}")
            self._send_message(
                chat_id, 
                f"❌ Ошибка при формировании отчета: {str(e)}"
            )
            return False
    
    def start(self):
        """Запуск бота"""
        if not self.is_running:
            logger.info("Запуск Telegram бота...")
            threading.Thread(
                target=self._run_bot,
                daemon=True
            ).start()
            self.is_running = True
    
    def _run_bot(self):
        """Запуск бота в отдельном потоке"""
        self.application.run_polling()
    
    def stop(self):
        """Остановка бота"""
        if self.is_running:
            logger.info("Остановка Telegram бота...")
            self.application.stop()
            self.is_running = False