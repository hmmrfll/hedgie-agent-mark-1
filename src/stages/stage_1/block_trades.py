# src/stages/stage_1/block_trades.py

from typing import Dict, List, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BlockTradesAnalyzer:
    """Анализатор блочных сделок"""
    
    def __init__(self, tools, memory, communicator):
        self.tools = tools
        self.memory = memory
        self.communicator = communicator

    def analyze(self, currency: str, days: int) -> Dict[str, Any]:
        """Выполнение анализа блочных сделок"""
        # Сбор данных
        trades = self._collect_data(currency, days)
        
        # Анализ данных
        analyzed_trades = self._analyze_data(trades)
        
        # Формирование результатов
        results = self._prepare_results(analyzed_trades)
        
        return results

    def _collect_data(self, currency: str, days: int) -> List[Dict[str, Any]]:
        """Сбор данных о сделках"""
        self.communicator.say("Получаю данные о сделках...")
        
        trades = self.tools.get_trades(currency, days)
        self.memory.update_context({'raw_trades': trades})
        
        self.communicator.say(f"Найдено {len(trades)} сделок за последние {days} дней")
        return trades

    def _analyze_data(self, trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Анализ собранных данных"""
        self.communicator.say("Начинаю анализ данных...")
        
        analyzed_trades = []
        for trade in trades:
            try:
                # Парсинг инструмента
                instrument_info = self.tools.parse_instrument(trade['instrument_name'])
                
                # Подготовка параметров для расчета дельты
                params = {
                    'current_price': float(trade['index_price']),
                    'strike': float(instrument_info.strike),
                    'expiry_date': instrument_info.expiry_date,
                    'volatility': float(trade['iv']),
                    'option_type': instrument_info.option_type
                }
                
                # Расчет метрик
                metrics = self.tools.calculate_delta(**params)
                
                if metrics:
                    trade['metrics'] = metrics
                    trade['instrument_info'] = instrument_info
                    analyzed_trades.append(trade)

            except Exception as e:
                logger.warning(f"Ошибка анализа сделки: {e}")
                continue

        return analyzed_trades

    def _prepare_results(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Подготовка результатов анализа"""
        if not trades:
            return {'status': 'no_data'}

        # Группировка по типам опционов
        calls = [t for t in trades if t['instrument_info'].option_type == 'C']
        puts = [t for t in trades if t['instrument_info'].option_type == 'P']

        # Расчет метрик
        total_delta = sum(t['metrics'].delta * float(t['amount']) for t in trades)
        call_volume = sum(float(t['amount']) for t in calls)
        put_volume = sum(float(t['amount']) for t in puts)

        # Анализ стратегий
        strategy_analysis = self.tools.analyze_strategies(trades)

        return {
            'total_trades': len(trades),
            'calls_count': len(calls),
            'puts_count': len(puts),
            'total_delta': total_delta,
            'call_volume': call_volume,
            'put_volume': put_volume,
            'strategy_analysis': strategy_analysis,
            'timestamp': datetime.now()
        }