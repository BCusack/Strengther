from pydantic import BaseModel
from datetime import datetime

# Define your data models here

class SymbolDataBase(BaseModel):
    symbol: str
    open: float
    high: float
    low: float
    close: float
    daily_change: float

class SymbolData(SymbolDataBase):
    last_updated: datetime
