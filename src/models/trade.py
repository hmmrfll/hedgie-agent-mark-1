from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, NamedTuple
import re

class InstrumentInfo(NamedTuple):
    asset: str          # BTC
    expiration: str     # 15JUL
    strike: int         # 78000
    option_type: str    # C или P

@dataclass
class Trade:
    timestamp: datetime
    contracts: Decimal
    tick_direction: int
    mark_price: Decimal
    amount: Decimal
    trade_seq: int
    index_price: Decimal
    price: Decimal
    iv: Decimal
    block_trade_leg_count: str
    instrument_name: str
    block_trade_id: str
    combo_id: Optional[str]
    liquidation: str
    direction: str
    combo_trade_id: Optional[str]
    trade_id: str
    _parsed_instrument: Optional[InstrumentInfo] = None

    def parse_instrument_name(self) -> InstrumentInfo:
        """Разбор instrument_name на составляющие"""
        if self._parsed_instrument:
            return self._parsed_instrument
            
        # Обновленный паттерн для разбора строки формата BTC-28FEB25-105000-C
        pattern = r"(\w+)-(\d+[A-Z]+\d+)-(\d+)-([CP])"
        match = re.match(pattern, self.instrument_name)
        
        if not match:
            logger.error(f"Не удалось разобрать instrument_name: {self.instrument_name}")
            # Возвращаем дефолтные значения вместо вызова исключения
            return InstrumentInfo(
                asset=self.instrument_name.split('-')[0],
                expiration="UNKNOWN",
                strike=0,
                option_type="?"
            )
            
        asset, expiration, strike, option_type = match.groups()
        self._parsed_instrument = InstrumentInfo(
            asset=asset,
            expiration=expiration,
            strike=int(strike),
            option_type=option_type
        )
        
        return self._parsed_instrument

    @property
    def instrument_info(self) -> InstrumentInfo:
        """Свойство для получения разобранной информации об инструменте"""
        return self.parse_instrument_name()

    @classmethod
    def from_db_row(cls, row: dict) -> 'Trade':
        return cls(
            timestamp=row['timestamp'],
            contracts=Decimal(str(row['contracts'])),
            tick_direction=row['tick_direction'],
            mark_price=Decimal(str(row['mark_price'])),
            amount=Decimal(str(row['amount'])),
            trade_seq=row['trade_seq'],
            index_price=Decimal(str(row['index_price'])),
            price=Decimal(str(row['price'])),
            iv=Decimal(str(row['iv'])),
            block_trade_leg_count=row['block_trade_leg_count'],
            instrument_name=row['instrument_name'],
            block_trade_id=row['block_trade_id'],
            combo_id=row.get('combo_id'),
            liquidation=row['liquidation'],
            direction=row['direction'],
            combo_trade_id=row.get('combo_trade_id'),
            trade_id=row['trade_id']
        )