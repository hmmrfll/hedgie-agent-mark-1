# src/tools/data_loader.py

from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
from .database_connector import DatabaseConnector

logger = logging.getLogger(__name__)

class DataLoader:
    """Инструмент для загрузки данных из БД"""
    
    def __init__(self, db_connector: DatabaseConnector):
        self.db = db_connector

    def load_trades(self, currency: str, days: int) -> List[Dict[str, Any]]:
        """Загрузка сделок за указанный период"""
        table_name = f"{currency.lower()}_block_trades"
        
        query = f"""
            SELECT 
                timestamp,
                contracts,
                tick_direction,
                mark_price,
                amount,
                trade_seq,
                index_price,
                price,
                iv,
                block_trade_leg_count,
                instrument_name,
                block_trade_id,
                combo_id,
                liquidation,
                direction,
                combo_trade_id,
                trade_id
            FROM {table_name}
            WHERE timestamp >= NOW() - INTERVAL '%s days'
            ORDER BY timestamp DESC
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (days,))
            return cursor.fetchall()

    def get_latest_trades(self, currency: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение последних сделок"""
        table_name = f"{currency.lower()}_block_trades"
        
        query = f"""
            SELECT *
            FROM {table_name}
            ORDER BY timestamp DESC
            LIMIT %s
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (limit,))
            return cursor.fetchall()

    def get_trades_by_date_range(self, currency: str, 
                               start_date: datetime, 
                               end_date: datetime) -> List[Dict[str, Any]]:
        """Загрузка сделок за указанный диапазон дат"""
        table_name = f"{currency.lower()}_block_trades"
        
        query = f"""
            SELECT *
            FROM {table_name}
            WHERE timestamp BETWEEN %s AND %s
            ORDER BY timestamp DESC
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (start_date, end_date))
            return cursor.fetchall()