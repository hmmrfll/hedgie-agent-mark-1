# main.py (исправленная версия)
import logging
from telegram import Update
from src.agent.base import TradingAgent
from src.tools.telegram_bot import TelegramBot
from src.config.settings import TELEGRAM_TOKEN, TELEGRAM_ALLOWED_USERS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    try:
        # Инициализация агента (без openai_api_key)
        agent = TradingAgent(
            telegram_token=TELEGRAM_TOKEN,
            telegram_chat_ids=None  # Бот будет отвечать всем
        )

        # Инициализация и запуск Telegram-бота
        bot = TelegramBot(token=TELEGRAM_TOKEN)
        bot.set_agent(agent)

        logger.info("Запуск Telegram бота...")
        # Запускаем бота
        bot.application.run_polling()

    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения.")
    except Exception as e:
        logger.error(f"Ошибка в основном процессе: {e}")
    finally:
        logger.info("Программа завершена.")

if __name__ == "__main__":
    main()
