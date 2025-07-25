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


class VolumeCache:
    def __init__(self):
        self.cache: Dict[str, SymbolChangeData] = {}
        self.last_hour: int = datetime.now(tz=pytz.utc).hour

    def get(self, symbol: str) -> SymbolChangeData | None:
        if self.last_hour != datetime.now(tz=pytz.utc).hour:
            self.cache.clear()
            self.last_hour = datetime.now(tz=pytz.utc).hour
        return self.cache.get(symbol)

    def set(self, symbol: str, volume_change: float):
        self.cache[symbol] = SymbolChangeData(
            symbol=symbol,
            open=0,
            high=0,
            low=0,
            close=0,
            last_updated=datetime.now(tz=pytz.utc),
            change=volume_change
        )


volume_cache = VolumeCache()


def process_symbol(symbol) -> SymbolChangeData | None:
    max_retries = 5
    base_sleep_time = 1  # Base sleep time in seconds
    total_period = 120
    for attempt in range(max_retries):
        try:
            # Fetch the last minutes of 1-minute kline data for volume comparison
            kline_data = client.get_kline(
                symbol=symbol,
                interval='1',  # 1-minute interval
                limit=total_period  # Last n periods (n recent + n prior)
            )["result"]["list"]

            # Check if we have at least n periods of data for volume comparison
            if not kline_data or len(kline_data) < total_period:
                return None

            # turn kline_data into a list of Klines
            kline_data = [Kline.from_list(kline) for kline in kline_data]

            # Calculate volume change: ((sum last 60 min - sum prior 60 min) / sum prior 60 min) * 100
            if len(kline_data) >= total_period:
                # Get the last n minutes of volume (most recent)
                last_volumes = [float(kline.volume) for kline in kline_data[0:total_period // 2]]
                sum_last = sum(last_volumes)

                # Get the prior n minutes of volume (n-30 periods ago)
                prior_volumes = [float(kline.volume) for kline in kline_data[total_period // 2:total_period]]
                sum_prior = sum(prior_volumes)

                # Calculate volume percentage change
                if sum_prior > 0:
                    change = ((sum_last - sum_prior) / sum_prior) * 100
                else:
                    change = 0
            else:
                # Not enough data for n-period volume comparison
                change = 0

            # Use the most recent kline for current price data
            recent_kline = kline_data[0]
            current_price = float(recent_kline.close)
            start_kline = kline_data[-1]

            # Create and return a SymbolData instance with the calculated volume change
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
    # Sort by absolute volume change percentage (highest 60min vs 60min volume changes first)
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
