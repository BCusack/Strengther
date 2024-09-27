import uvicorn
from src.background_process import run_background_task
import threading
from fastapi import FastAPI
from src.api import router as api_router
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global background_thread
    background_thread = threading.Thread(target=run_background_task, daemon=True)
    background_thread.start()
    yield
    if background_thread:
        # Implement a way to stop your background task gracefully
        pass

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
