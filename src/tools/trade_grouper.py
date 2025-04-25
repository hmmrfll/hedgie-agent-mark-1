# src/tools/trade_grouper.py

from typing import List, Dict, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class TradeGrouper:
    """Инструмент для группировки и анализа связанных сделок"""

    def group_by_block_trade(self, trades: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Группировка сделок по block_trade_id

        Args:
            trades: Список сделок

        Returns:
            Dict[str, List[Dict]]: Сгруппированные сделки по block_trade_id
        """
        grouped_trades = defaultdict(list)
        
        for trade in trades:
            block_id = trade.get('block_trade_id')
            if block_id:
                grouped_trades[block_id].append(trade)
            else:
                logger.debug(f"Сделка без block_trade_id: {trade.get('trade_id')}")

        return dict(grouped_trades)

    def analyze_block_trades(self, grouped_trades: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Анализ блочных сделок

        Args:
            grouped_trades: Сгруппированные сделки

        Returns:
            Dict: Результаты анализа
        """
        analysis = {
            'total_blocks': len(grouped_trades),
            'trades_in_blocks': sum(len(trades) for trades in grouped_trades.values()),
            'blocks_by_size': {},
            'largest_blocks': [],
            'complex_strategies': []
        }

        # Анализ размеров блоков
        for block_id, trades in grouped_trades.items():
            size = len(trades)
            analysis['blocks_by_size'][size] = analysis['blocks_by_size'].get(size, 0) + 1

            # Находим крупнейшие блоки
            total_amount = sum(float(trade.get('amount', 0)) for trade in trades)
            analysis['largest_blocks'].append({
                'block_id': block_id,
                'size': size,
                'total_amount': total_amount,
                'trades': trades
            })

            # Определяем сложные стратегии (более 2 сделок в блоке)
            if size > 2:
                analysis['complex_strategies'].append({
                    'block_id': block_id,
                    'size': size,
                    'trades': trades
                })

        # Сортируем крупнейшие блоки по размеру
        analysis['largest_blocks'] = sorted(
            analysis['largest_blocks'],
            key=lambda x: x['total_amount'],
            reverse=True
        )[:5]  # Оставляем топ-5

        return analysis

    def get_block_strategy(self, trades: List[Dict[str, Any]]) -> str:
        """
        Определение типа стратегии по сделкам в блоке

        Args:
            trades: Список сделок в блоке

        Returns:
            str: Название стратегии
        """
        if len(trades) == 2:
            # Определяем типы опционов
            types = [trade['instrument_info'].option_type for trade in trades]
            strikes = [trade['instrument_info'].strike for trade in trades]
            
            if 'C' in types and 'P' in types:
                if len(set(strikes)) == 1:
                    return "Straddle"
                else:
                    return "Risk Reversal"
            elif types.count('C') == 2:
                return "Call Spread"
            elif types.count('P') == 2:
                return "Put Spread"
                
        elif len(trades) == 4:
            return "Iron Condor/Butterfly"
            
        return "Complex Strategy"