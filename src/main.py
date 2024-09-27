from pybit.unified_trading import HTTP
from typing import Dict, List
import os
from datetime import datetime

import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.models import SymbolData

from colorama import init
import pandas as pd
import pytz


# Initialize the HTTP client
api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")
client = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)

init(autoreset=True)


class PriceCache:
    def __init__(self):
        self.cache: Dict[str, SymbolData] = {}
        self.last_hour: datetime = datetime.now(tz=pytz.utc).hour

    def get(self, symbol: str) -> SymbolData | None:
        if self.last_hour != datetime.now(tz=pytz.utc).hour:
            self.cache.clear()
            self.last_hour = datetime.now(tz=pytz.utc).hour
        return self.cache.get(symbol)

    def set(self, symbol: str, open_price: float):
        self.cache[symbol] = SymbolData(
            symbol=symbol,
            open_price=open_price,
            high_price=0,
            low_price=0,
            close_price=0,
            last_updated=datetime.now(tz=pytz.utc),
            daily_change=0
        )
        
    

price_cache = PriceCache()


def process_symbol(symbol) -> SymbolData | None:
    try:
        # Fetch the last two days of 1-day kline data
        kline_data = client.get_kline(
            symbol=symbol,
            interval='D',  # 1-day interval
            limit=2  # Last two days
        )["result"]["list"]
        
        # Check if we have at least two days of data to calculate the change
        if not kline_data or len(kline_data) < 2:
            return None
        
        # Use the second last kline for the previous day's close price
        previous_day_kline = kline_data[1]
        previous_close_price = float(previous_day_kline[4])
        
        # Use the most recent kline for the current price
        recent_kline = kline_data[0]
        current_price = float(recent_kline[4])
        
        # Calculate the daily change
        daily_change = ((current_price - previous_close_price) / previous_close_price) * 100
        
        # Create and return a SymbolData instance with the calculated daily change
        return SymbolData(
            symbol=symbol,
            open=float(recent_kline[1]),
            high=float(recent_kline[2]),
            low=float(recent_kline[3]),
            close=current_price,
            last_updated=datetime.now(tz=pytz.utc),
            daily_change=daily_change
        )
    except Exception as e:
        print(f"Error processing {symbol}: {str(e)}")
        return None

async def get_perpetual_futures_daily_data() -> List[SymbolData]:
    instruments = client.get_instruments_info(category="linear")["result"]["list"]
    symbols = [instrument["symbol"] for instrument in instruments]
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(executor, process_symbol, symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)

    _data = [r for r in results if r is not None]
    _data.sort(key=lambda x: abs(x.daily_change), reverse=True)
    
    return _data

def get_data():
    # This is a synchronous wrapper for the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(get_perpetual_futures_daily_data())
    loop.close()
    df = pd.DataFrame([r.model_dump() for r in results])
    return df

# Remove the main execution part if you want to use this file only as a module