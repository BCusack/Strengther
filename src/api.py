from fastapi import APIRouter, Query
from typing import List
from src.models import SymbolData
import pandas as pd

router = APIRouter()


data_store: List[SymbolData] = []

def update_data(new_data: pd.DataFrame):
    global data_store
    data_store = [SymbolData(**row) for row in new_data.to_dict('records')]

@router.get("/data", response_model=List[SymbolData])
async def get_data():
    return data_store

@router.get("/top", response_model=List[SymbolData])
async def get_top_symbols(n: int = Query(5, ge=1, le=100)):
    return sorted(data_store, key=lambda x: abs(x.pva), reverse=True)[:n]
