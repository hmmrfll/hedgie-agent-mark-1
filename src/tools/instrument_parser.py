# src/tools/instrument_parser.py

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class InstrumentInfo:
    asset: str        # BTC/ETH
    expiration: str   # 28MAR25
    strike: float     # 110000
    option_type: str  # C/P
    expiry_date: Optional[datetime] = None

class InstrumentParser:
    """Инструмент для парсинга имен опционных инструментов"""
    
    @staticmethod
    def parse(instrument_name: str) -> InstrumentInfo:
        """Разбор имени инструмента на компоненты"""
        try:
            parts = instrument_name.split("-")
            asset = parts[0]
            expiration = parts[1]
            strike = float(parts[2])
            option_type = parts[3]
            
            # Преобразование даты экспирации
            expiry_date = datetime.strptime(expiration, '%d%b%y')
            
            return InstrumentInfo(
                asset=asset,
                expiration=expiration,
                strike=strike,
                option_type=option_type,
                expiry_date=expiry_date
            )
        except Exception as e:
            raise ValueError(f"Ошибка парсинга инструмента {instrument_name}: {e}")

    @staticmethod
    def validate(info: InstrumentInfo) -> bool:
        """Проверка корректности данных инструмента"""
        return (
            info.asset in ['BTC', 'ETH'] and
            info.option_type in ['C', 'P'] and
            info.strike > 0 and
            info.expiry_date > datetime.now()
        )