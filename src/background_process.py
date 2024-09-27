import asyncio
import pandas as pd
from src.main import  get_perpetual_futures_daily_data 
from src.api import update_data
import time
import logging
from colorama import Fore, Style, init

init(autoreset=True)  # Initialize colorama

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def background_task():
    while True:
        start_time = time.time()
        try:
            results = await get_perpetual_futures_daily_data()
            df = pd.DataFrame([r.model_dump() for r in results])
            update_data(df)
            duration = time.time() - start_time
            print(f"{Fore.BLUE}{time.strftime('%Y-%m-%d %H:%M:%S')} - INFO - Background task completed. Cycle duration: {duration:.2f} seconds{Style.RESET_ALL}")
            await asyncio.sleep(1)  # Wait for the remainder of the hour
        except Exception as e:
            print(f"{Fore.RED}{time.strftime('%Y-%m-%d %H:%M:%S')} - ERROR - Error in background task: {str(e)}{Style.RESET_ALL}")
            await asyncio.sleep(3600)  # Wait for an hour before retrying

def run_background_task():
    asyncio.run(background_task())
