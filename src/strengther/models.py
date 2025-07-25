from datetime import time
from pydantic import BaseModel, Field, RootModel
from datetime import datetime


# Define your data models here

class SymbolBase(BaseModel):
    symbol: str
    open: float
    high: float
    low: float
    close: float


class Kline(BaseModel):
    start_time: str  # Start time of the kline (timestamp as string)
    open: str        # Open price (as string from API)
    high: str        # High price (as string from API)
    low: str         # Low price (as string from API)
    close: str       # Close price (as string from API)
    volume: str      # Volume (as string from API)
    turnover: str    # Turnover (as string from API)

    @classmethod
    def from_list(cls, data: list) -> 'Kline':
        """Create a Kline from the Bybit API response list format"""
        if len(data) < 7:
            raise ValueError(f"Expected at least 7 elements in kline data, got {len(data)}")

        return cls(
            start_time=data[0],
            open=data[1],
            high=data[2],
            low=data[3],
            close=data[4],
            volume=data[5],
            turnover=data[6]
        )


class SymbolChangeData(SymbolBase):
    change: float
    last_updated: datetime


class SymbolChangeDataList(RootModel[list[SymbolChangeData]]):
    root: list[SymbolChangeData] = Field(..., description="List of SymbolChangeData objects")


class SessionData(SymbolChangeData):
    session_name: str


class SessionInfo(BaseModel):
    start_time_utc: time = Field(..., description="Session start time in UTC as Unix timestamp in milliseconds")
    name: str = Field(..., description="Name of the session")
    duration_hours: float = Field(..., description="Duration of the session in hours")
    # candle_data: SymbolChangeDataList = Field(..., description="Candle data for the session, e.g., {'open': 0.0, 'high': 0.0, 'low': 0.0, 'close': 0.0}")
