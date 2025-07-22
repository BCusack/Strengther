from datetime import time
from typing import Dict
from pydantic import BaseModel, Field, RootModel
from datetime import datetime


# Define your data models here

class SymbolBase(BaseModel):
    symbol: str
    open: float
    high: float
    low: float
    close: float


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
