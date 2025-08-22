# app/utils.py
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

def to_money(value) -> Decimal:
    return (Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def now_ts() -> datetime:
    return datetime.now()
