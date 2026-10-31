"""Tests for the WebSocket data validators (src/utils/data_validators.py)."""
import pytest
from pydantic import ValidationError

from src.utils.data_validators import DepthData, KlineData


def kline(**overrides):
    data = dict(
        timestamp=1_700_000_000_000,
        open=100.0,
        high=105.0,
        low=95.0,
        close=102.0,
        volume=10.0,
        is_closed=True,
    )
    data.update(overrides)
    return KlineData(**data)


class TestKlineData:
    def test_valid_candle_is_accepted(self):
        assert kline().close == 102.0

    def test_flat_candle_is_accepted(self):
        assert kline(open=100, high=100, low=100, close=100).high == 100

    def test_close_above_high_is_rejected(self):
        # Regression: close was never compared with high, because the `high`
        # validator ran before `close` had been parsed.
        with pytest.raises(ValidationError):
            kline(close=110.0)

    def test_close_below_low_is_rejected(self):
        # Regression: same field-order bug on the `low` side.
        with pytest.raises(ValidationError):
            kline(close=90.0)

    def test_high_below_low_is_rejected(self):
        with pytest.raises(ValidationError):
            kline(high=94.0, low=95.0, open=94.5, close=94.5)

    def test_open_above_high_is_rejected(self):
        with pytest.raises(ValidationError):
            kline(open=106.0)

    def test_open_below_low_is_rejected(self):
        with pytest.raises(ValidationError):
            kline(open=94.0)

    def test_non_positive_price_is_rejected(self):
        with pytest.raises(ValidationError):
            kline(low=0)

    def test_extra_binance_fields_are_ignored(self):
        assert not hasattr(kline(trades=42), "trades")


class TestDepthData:
    def test_valid_book_is_accepted(self):
        book = DepthData(timestamp=1, bids=[(99.0, 1.0)], asks=[(101.0, 1.0)])
        assert book.asks[0][0] == 101.0

    def test_crossed_book_is_rejected(self):
        with pytest.raises(ValidationError):
            DepthData(timestamp=1, bids=[(101.0, 1.0)], asks=[(99.0, 1.0)])

    def test_negative_quantity_is_rejected(self):
        with pytest.raises(ValidationError):
            DepthData(timestamp=1, bids=[(99.0, -1.0)], asks=[(101.0, 1.0)])
