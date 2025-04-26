# src/tools/strategy_analyzer.py

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class StrategyAnalyzer:
    """Инструмент для анализа опционных стратегий"""

    def identify_strategy(self, combo_id: str) -> str:
        """
        Определение типа стратегии по combo_id
        """
        if not combo_id:
            return "Single Trade"

        if "RR" in combo_id:
            return "Risk Reversal"
        elif "STRD" in combo_id:
            return "Straddle"
        elif "BF" in combo_id:
            return "Butterfly"
        elif "IC" in combo_id:
            return "Iron Condor"
        elif "CS" in combo_id:
            return "Call Spread"
        elif "PS" in combo_id:
            return "Put Spread"

        return "Unknown Strategy"

    def analyze_strategies(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Анализ стратегий в сделках
        """
        strategies = {}
        strategy_stats = {
            'total_strategies': 0,
            'by_type': {},
            'volume_by_type': {},
            'largest_trades': []
        }

        # Группировка по combo_id
        for trade in trades:
            combo_id = trade.get('combo_id')
            strategy_type = self.identify_strategy(combo_id)

            if strategy_type not in strategies:
                strategies[strategy_type] = []
            strategies[strategy_type].append(trade)

        # Сбор статистики
        for strategy_type, strategy_trades in strategies.items():
            total_volume = sum(float(trade.get('amount', 0)) for trade in strategy_trades)

            strategy_stats['by_type'][strategy_type] = len(strategy_trades)
            strategy_stats['volume_by_type'][strategy_type] = total_volume
            strategy_stats['total_strategies'] += len(strategy_trades)

            # Сохраняем крупные сделки
            strategy_stats['largest_trades'].extend([
                {
                    'type': strategy_type,
                    'amount': float(trade.get('amount', 0)),
                    'combo_id': trade.get('combo_id'),
                    'trade_id': trade.get('trade_id')
                }
                for trade in strategy_trades
                if float(trade.get('amount', 0)) > 100  # Порог для крупных сделок
            ])

        # Сортируем крупные сделки по объему
        strategy_stats['largest_trades'].sort(key=lambda x: x['amount'], reverse=True)
        strategy_stats['largest_trades'] = strategy_stats['largest_trades'][:15]  # Top 5

        return {
            'strategies': strategies,
            'stats': strategy_stats
        }

    def get_strategy_description(self, strategy_type: str) -> str:
        """
        Получение описания стратегии
        """
        descriptions = {
            'Risk Reversal': 'Комбинация длинного CALL и короткого PUT опционов',
            'Straddle': 'Покупка CALL и PUT опционов с одинаковым страйком',
            'Butterfly': 'Комбинация из четырех опционов для ограничения риска',
            'Iron Condor': 'Нейтральная стратегия с ограниченным риском',
            'Call Spread': 'Спред с использованием CALL опционов',
            'Put Spread': 'Спред с использованием PUT опционов',
            'Single Trade': 'Одиночная сделка',
            'Unknown Strategy': 'Неизвестная стратегия'
        }
        return descriptions.get(strategy_type, 'Описание отсутствует')
