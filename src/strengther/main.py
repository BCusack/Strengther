import random
from pybit.unified_trading import HTTP
from typing import Dict, List, Set
from datetime import datetime
from time import sleep

import asyncio
from concurrent.futures import ThreadPoolExecutor
from strengther.models import SymbolChangeData, Kline

from colorama import init
import pandas as pd
import pytz
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Set up the logging level for the pybit library
logging.getLogger('pybit').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# In-memory store for the symbols. A set provides fast lookups and automatic deduplication.
_symbols: Set[str] = set()

# Initialize the HTTP client
api_key = "S0LVZJkjNAtKUhjkcJ"
api_secret = "xVLxQRudWZB82c9spyBDc8L92njzLxVFASjk"
client = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)

init(autoreset=True)


class PriceCache:
    def __init__(self):
        self.cache: Dict[str, SymbolChangeData] = {}
        self.last_hour: int = datetime.now(tz=pytz.utc).hour

    def get(self, symbol: str) -> SymbolChangeData | None:
        if self.last_hour != datetime.now(tz=pytz.utc).hour:
            self.cache.clear()
            self.last_hour = datetime.now(tz=pytz.utc).hour
        return self.cache.get(symbol)

    def set(self, symbol: str, open_price: float):
        self.cache[symbol] = SymbolChangeData(
            symbol=symbol,
            open=open_price,
            high=0,
            low=0,
            close=0,
            last_updated=datetime.now(tz=pytz.utc),
            change=0
        )


price_cache = PriceCache()


def process_symbol(symbol) -> SymbolChangeData | None:
    max_retries = 5
    base_sleep_time = 1  # Base sleep time in seconds
    for attempt in range(max_retries):
        try:
            # Fetch the last two days of 1-day kline data
            kline_data = client.get_kline(
                symbol=symbol,
                interval='1',  # 1-minute interval
                limit=60  # Last 60 periods
            )["result"]["list"]

            # Check if we have at least two periods of data to calculate the change
            if not kline_data or len(kline_data) < 2:
                return None

            # turn kline_data into a list of Klines
            kline_data = [Kline.from_list(kline) for kline in kline_data]

            # Use the last kline for the previous period's close price
            start_kline = kline_data[-1]
            open_price = float(start_kline.open)

            # Use the most recent kline for the current price
            recent_kline = kline_data[0]
            current_price = float(recent_kline.close)

            # Calculate the daily change
            change = ((current_price - open_price) / open_price) * 100

            # Create and return a SymbolData instance with the calculated daily change
            return SymbolChangeData(
                symbol=symbol,
                open=float(start_kline.open),
                high=float(start_kline.high),
                low=float(start_kline.low),
                close=current_price,
                last_updated=datetime.now(tz=pytz.utc),
                change=change
            )
        except Exception as e:
            print(f"Error processing {symbol}: {str(e)}")
            if "rate limit" in str(e).lower():
                # Implement exponential backoff
                sleep_time = base_sleep_time * (2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limit hit. Retrying in {sleep_time:.2f} seconds...")
                sleep(sleep_time)
            else:
                sleep(10)
                print("Retrying in 10 seconds...")
    return None


async def update_symbols():
    """
    Fetches all linear perpetual symbols ending in 'USDT' from the exchange
    and updates the in-memory set.
    """
    logger.info("Attempting to update symbol list...")
    try:
        global _symbols
        temp_symbols = set()
        # Initial fetch
        res = client.get_instruments_info(category="linear")
        response_data = res[0] if isinstance(res, tuple) else res
        instruments = response_data.get("result", {}).get("list", [])
        next_page_cursor = response_data.get("result", {}).get("nextPageCursor", "")

        for instrument in instruments:
            if instrument.get('symbol', '').endswith("USDT"):
                temp_symbols.add(instrument['symbol'])

        # Paginate if necessary
        while next_page_cursor:
            await asyncio.sleep(0.2)  # Small delay to respect rate limits
            res = client.get_instruments_info(category="linear", cursor=next_page_cursor)
            response_data = res[0] if isinstance(res, tuple) else res
            instruments = response_data.get("result", {}).get("list", [])
            next_page_cursor = response_data.get("result", {}).get("nextPageCursor", "")
            for instrument in instruments:
                if instrument.get('symbol', '').endswith("USDT"):
                    temp_symbols.add(instrument['symbol'])

        if temp_symbols:
            _symbols = temp_symbols
            logger.info(f"Successfully updated symbol list. Found {len(_symbols)} symbols.")
        else:
            logger.warning("Symbol update resulted in an empty list. Retaining old list.")

    except Exception as e:
        logger.error(f"Failed to update symbol list: {e}")


def get_symbols() -> List[str]:
    """
    Returns the current list of available symbols, sorted alphabetically.
    """
    return sorted(list(_symbols))


async def get_perpetual_futures_daily_data() -> List[SymbolChangeData]:

    with ThreadPoolExecutor(max_workers=10) as executor:
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(executor, process_symbol, symbol) for symbol in _symbols]
        results = await asyncio.gather(*tasks)

    _data = [r for r in results if r is not None]
    _data.sort(key=lambda x: abs(x.change), reverse=True)

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
