from pybit.unified_trading import HTTP
from typing import Dict, List
import os
from datetime import datetime
from pydantic import BaseModel
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
from colorama import init, Fore, Style
import pandas as pd


# Initialize the HTTP client
api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")
client = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)

init(autoreset=True)

class SymbolData(BaseModel):
    symbol: str
    open_price: float
    last_updated: datetime

class ChangeFromOpen(BaseModel):
    symbol: str
    change_from_open: float
    absChange: float

class PriceCache:
    def __init__(self):
        self.cache: Dict[str, SymbolData] = {}
        self.last_day: datetime = datetime.utcnow().date()

    def get(self, symbol: str) -> SymbolData | None:
        if self.last_day != datetime.utcnow().date():
            self.cache.clear()
            self.last_day = datetime.utcnow().date()
        return self.cache.get(symbol)

    def set(self, symbol: str, open_price: float):
        self.cache[symbol] = SymbolData(
            symbol=symbol,
            open_price=open_price,
            last_updated=datetime.utcnow()
        )

price_cache = PriceCache()

def process_symbol(symbol):
    try:
        cached_data = price_cache.get(symbol)
        if cached_data is None:
            now = datetime.utcnow()
            start_of_day = datetime(now.year, now.month, now.day)
            start_timestamp = int(start_of_day.timestamp() * 1000)
            
            kline_data = client.get_kline(
                category="linear",
                symbol=symbol,
                interval="D",
                start=start_timestamp,
                limit=1
            )["result"]["list"]
            
            if kline_data:
                open_price = float(kline_data[0][1])
                price_cache.set(symbol, open_price)
        else:
            open_price = cached_data.open_price

        ticker = ticker_dict.get(symbol, {})
        current_price = float(ticker.get("lastPrice", 0))
        
        if current_price == 0:
            return None
        
        change_from_open = ((current_price - open_price) / open_price) * 100
        abs_change = abs(change_from_open)
        
        return ChangeFromOpen(
            symbol=symbol,
            change_from_open=round(change_from_open, 2),
            absChange=round(abs_change, 2)
        )
    except Exception as e:
        print(f"Error processing {symbol}: {str(e)}")
        return None

async def get_perpetual_futures_change_from_open() -> List[ChangeFromOpen]:
    global ticker_dict  # Make ticker_dict accessible in process_symbol
    instruments = client.get_instruments_info(category="linear")["result"]["list"]
    symbols = [instrument["symbol"] for instrument in instruments]
    
    # Fetch all tickers at once
    all_tickers = client.get_tickers(category="linear")["result"]["list"]
    ticker_dict = {ticker["symbol"]: ticker for ticker in all_tickers}

    with ThreadPoolExecutor(max_workers=10) as executor:
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(executor, process_symbol, symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)

    changes_from_open = [r for r in results if r is not None]
    changes_from_open.sort(key=lambda x: x.absChange, reverse=True)
    
    return changes_from_open

def get_data():
    # This is a synchronous wrapper for the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(get_perpetual_futures_change_from_open())
    loop.close()
    df = pd.DataFrame([r.dict() for r in results])
    return df

# Remove the main execution part if you want to use this file only as a module