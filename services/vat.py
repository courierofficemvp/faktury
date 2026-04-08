from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

VATType = Literal['23%', '8%']
TWOPLACES = Decimal('0.01')


def to_decimal(value: str | float | int | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    normalized = str(value).replace(' ', '').replace(',', '.')
    return Decimal(normalized).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def calculate_vat_and_refund(brutto: Decimal, vat_rate: VATType) -> tuple[Decimal, Decimal]:
    brutto = to_decimal(brutto)
    if vat_rate == '23%':
        vat = (brutto * Decimal('23') / Decimal('123')).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    elif vat_rate == '8%':
        vat = (brutto * Decimal('8') / Decimal('108')).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    else:
        raise ValueError(f'Unsupported VAT rate: {vat_rate}')

    refund = (vat / Decimal('2')).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    return vat, refund
