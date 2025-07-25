import asyncio
import logging
import uvicorn
from strengther.main import update_symbols
from strengther.background_process import background_task

from fastapi import FastAPI
from strengther.api import router as api_router
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(_: FastAPI):
    logging.info("Application startup: Starting background tasks and scheduler.")
    await update_symbols()
    # Create the background task so it runs on the main event loop
    task = asyncio.create_task(background_task())

    yield
    
    # Clean up on shutdown
    logging.info("Application shutdown: Stopping background tasks and scheduler.")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logging.info("Background task was successfully cancelled.")


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Import and include routes after creating the FastAPI instance
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
