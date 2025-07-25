import asyncio
import pandas as pd
from strengther.main import get_perpetual_futures_daily_data
from strengther.api import update_data
import time
import logging
from colorama import Fore, Style, init

init(autoreset=True)  # Initialize colorama

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def background_task():
    while True:
        start_time = time.time()
        try:
            results = await get_perpetual_futures_daily_data()
            df = pd.DataFrame([r.model_dump() for r in results])
            update_data(df)
            duration = time.time() - start_time
            top_symbol = df.loc[df['change'].abs().idxmax()]
            logger.info(f"{Fore.GREEN}Top symbol: {top_symbol['symbol']} | Change: {top_symbol['change']:.2f} | "
                        f"Open: {top_symbol['open']} | High: {top_symbol['high']} | "
                        f"Low: {top_symbol['low']} | Close: {top_symbol['close']} | "
                        f"Duration: {duration:.2f} seconds{Style.RESET_ALL}")
            await asyncio.sleep(1)  # Wait before the next cycle
        except Exception as e:
            logger.error(f"Error in background task: {str(e)}")
            await asyncio.sleep(5)  # Wait longer on error
