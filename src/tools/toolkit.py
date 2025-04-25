# src/tools/toolkit.py

from typing import Dict, Any, List
from .database_connector import DatabaseConnector
from .data_loader import DataLoader
from .instrument_parser import InstrumentParser
from .options_calculator import OptionsCalculator
from .trade_grouper import TradeGrouper
from .strategy_analyzer import StrategyAnalyzer
from .news_analyzer import NewsAnalyzer
from .sentiment_analyzer import SentimentAnalyzer
from .price_data import PriceDataFetcher
from .technical_indicators import TechnicalIndicators
from .risk_calculator import RiskCalculator
from .report_generator import ReportGenerator
from .telegram_notifier import TelegramNotifier
from .gpt_handler import GPTHandler
from .ollama_handler import OllamaHandler


class ToolKit:
    """Набор инструментов для агента"""
    
    def __init__(self, telegram_token: str = None, telegram_chat_ids: List[str] = None):
        # Инициализация всех инструментов
        self.db_connector = DatabaseConnector(
            host="localhost",
            port=5433,
            database="deribit_trades",
            user="admin",
            password="admin123"
        )
        self.data_loader = DataLoader(self.db_connector)
        self.parser = InstrumentParser()
        self.calculator = OptionsCalculator()
        self.trade_grouper = TradeGrouper()
        self.strategy_analyzer = StrategyAnalyzer()  # Добавляем новый инструмент
        self.news_analyzer = NewsAnalyzer(api_key="b0832b75c50749ce9403f07a1c222120")  # API ключ нужно будет взять из конфига
        self.sentiment_analyzer = SentimentAnalyzer()  # Добавляем новый инструмент
        self.price_data_fetcher = PriceDataFetcher()
        self.technical_indicators = TechnicalIndicators()
        self.risk_calculator = RiskCalculator()
        self.report_generator = ReportGenerator()
        self.telegram_notifier = None

        self.ollama_handler = OllamaHandler(model_name="llama3")

        if telegram_token and telegram_chat_ids:
            self.telegram_notifier = TelegramNotifier(telegram_token, telegram_chat_ids)
        


    def get_trades(self, currency: str, days: int) -> Dict[str, Any]:
        """Получение сделок"""
        return self.data_loader.load_trades(currency, days)

    def parse_instrument(self, instrument_name: str) -> Dict[str, Any]:
        """Парсинг инструмента"""
        return self.parser.parse(instrument_name)

    def calculate_delta(self, **params):
        """Расчет дельты"""
        return self.calculator.calculate_delta(**params)

    def group_trades(self, trades: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Группировка сделок"""
        return self.trade_grouper.group_by_block_trade(trades)

    def analyze_blocks(self, grouped_trades: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Анализ блочных сделок"""
        return self.trade_grouper.analyze_block_trades(grouped_trades)

    def get_strategy(self, trades: List[Dict[str, Any]]) -> str:
        """Определение стратегии"""
        return self.trade_grouper.get_block_strategy(trades)
    
    def analyze_strategies(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ стратегий"""
        return self.strategy_analyzer.analyze_strategies(trades)

    def get_strategy_type(self, combo_id: str) -> str:
        """Определение типа стратегии"""
        return self.strategy_analyzer.identify_strategy(combo_id)

    def get_strategy_description(self, strategy_type: str) -> str:
        """Получение описания стратегии"""
        return self.strategy_analyzer.get_strategy_description(strategy_type)
    
    def get_news(self, currency: str, days: int) -> Dict[str, Any]:
        """Получение новостей"""
        return self.news_analyzer.get_news(currency, days)

    def analyze_news(self, articles: List[Dict], currency: str) -> Dict[str, Any]:
        """Анализ новостей"""
        return self.news_analyzer.analyze_sentiment(articles, currency)
    
    def analyze_sentiment(self, articles: List[Dict], currency: str) -> Dict[str, Any]:
        """Анализ тональности текста с BERT"""
        return self.sentiment_analyzer.analyze_news(articles, currency)
    
    def get_historical_data(self, currency: str, days: int, interval: str = '1d') -> Dict[str, Any]:
        """Получение исторических данных"""
        return self.price_data_fetcher.get_historical_data(currency, days, interval)
    
    def calculate_rsi(self, prices, window=14):
        """Расчет RSI"""
        return self.technical_indicators.calculate_rsi(prices, window)
    
    def calculate_sma(self, prices, window):
        """Расчет SMA"""
        return self.technical_indicators.calculate_sma(prices, window)
    
    def calculate_ema(self, prices, window):
        """Расчет EMA"""
        return self.technical_indicators.calculate_ema(prices, window)
    
    def calculate_macd(self, prices, fast_period=12, slow_period=26, signal_period=9):
        """Расчет MACD"""
        return self.technical_indicators.calculate_macd(prices, fast_period, slow_period, signal_period)
    
    def calculate_bollinger_bands(self, prices, window=20, num_std=2):
        """Расчет полос Боллинджера"""
        return self.technical_indicators.calculate_bollinger_bands(prices, window, num_std)
    
    def calculate_var_monte_carlo(self, returns, confidence_level=0.95, simulations=10000, time_horizon=1):
        """Расчет Value at Risk (VaR) методом Монте-Карло"""
        return self.risk_calculator.calculate_var_monte_carlo(
            returns, confidence_level, simulations, time_horizon
        )
    
    def calculate_volatility(self, returns):
        """Расчет волатильности"""
        return self.risk_calculator.calculate_volatility(returns)
    
    def calculate_sharpe_ratio(self, returns, risk_free_rate=0.0):
        """Расчет коэффициента Шарпа"""
        return self.risk_calculator.calculate_sharpe_ratio(returns, risk_free_rate)
    
    def calculate_position_size(self, capital, max_risk_percent, stop_loss_percent, volatility_percent):
        """Расчет оптимального размера позиции"""
        return self.risk_calculator.calculate_position_size(
            capital, max_risk_percent, stop_loss_percent, volatility_percent
        )

    def recommend_stop_loss(self, current_price, volatility_percent):
        """Рекомендации по стоп-лоссу"""
        return self.risk_calculator.recommend_stop_loss(current_price, volatility_percent)
    def generate_latex_report(self, data, template_path=None):
        """Генерация отчета в формате LaTeX"""
        return self.report_generator.generate_latex_report(data, template_path)
    
    def generate_charts(self, data):
        """Генерация графиков для отчета"""
        return self.report_generator.generate_charts(data)
    
    def send_telegram_message(self, message: str) -> bool:
        """Отправка сообщения в Telegram"""
        if self.telegram_notifier:
            return self.telegram_notifier.send_message(message)
        return False
    
    def send_telegram_report(self, analysis_data: Dict[str, Any]) -> bool:
        """Отправка отчета в Telegram"""
        if self.telegram_notifier:
            return self.telegram_notifier.send_analysis_report(analysis_data)
        return False
    
    def ask_gpt(self, question: str, analysis_data: Dict[str, Any]) -> str:
        """Получение ответа от GPT"""
        if hasattr(self, 'gpt_handler') and self.gpt_handler:
            return self.gpt_handler.get_answer(question, analysis_data)
        else:
            return "❌ GPT не инициализирован или недоступен. Используется Ollama."

    def ask_ollama(self, question: str, analysis_data: Dict[str, Any]) -> str:
        """Получение ответа от локальной модели Ollama"""
        if hasattr(self, 'ollama_handler') and self.ollama_handler:
            return self.ollama_handler.get_answer(question, analysis_data)
        else:
            return "❌ Модуль Ollama не инициализирован или недоступен."