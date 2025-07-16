
from fastapi import APIRouter, Query
from typing import List
from strengther.main import get_symbols
from strengther.models import SymbolChangeData
import pandas as pd

router = APIRouter()


data_store: List[SymbolChangeData] = []


def update_data(new_data: pd.DataFrame):
    global data_store
    data_store = [SymbolChangeData(**{str(k): v for k, v in row.items()}) for row in new_data.to_dict('records')]


@router.get("/data", response_model=List[SymbolChangeData])
async def get_data():
    return data_store


@router.get("/top", response_model=List[SymbolChangeData])
async def get_top_symbols(n: int = Query(5, ge=1, le=100)):
    return sorted(data_store, key=lambda x: abs(float(x.pva)), reverse=True)[:n]


@router.get("/health_check", response_model=str)
async def health_check():
    # send BYBIT_API_KEY
    return 'Version: 🌴🌴'


@router.get("/symbols", response_model=List[str])
async def list_available_symbols():
    """
    Returns a list of all available USDT perpetual futures symbols.
    """
    return get_symbols()