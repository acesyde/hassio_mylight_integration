"""Unit conversion constants and helpers for MyLight Systems."""

WS_TO_WH: float = 3600.0  # Watt-seconds to Watt-hours
W_TO_KW: float = 1000.0  # Watts to Kilowatts


def ws_to_wh(value: float) -> float:
    """Convert Watt-seconds to Watt-hours."""
    return value / WS_TO_WH


def ws_to_kwh(value: float) -> float:
    """Convert Watt-seconds to Kilowatt-hours."""
    return value / WS_TO_WH / W_TO_KW
