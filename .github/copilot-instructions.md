# Strengther AI Coding Agent Instructions

This document provides guidance for AI coding agents working on the Strengther codebase.

## Architecture Overview

Strengther is a Python-based application that fetches cryptocurrency market data from the Bybit exchange, calculates daily price changes, and exposes this data via a FastAPI REST API.

The application consists of several key components:

- **FastAPI Application (`src/strengther/app.py`):** The main entry point for the web application. It initializes the FastAPI app, sets up CORS middleware, and manages the application's lifespan. A background task is started on application startup to periodically refresh the market data.

- **API Endpoints (`src/strengther/api.py`):** Defines all the API routes. The data is served from an in-memory list of `SymbolChangeData` objects (`data_store`) which is updated by the background process.

- **Bybit Data Fetching (`src/strengther/main.py`):** This module contains the core logic for interacting with the Bybit API using the `pybit` library.

  - `update_symbols()`: Fetches and maintains a list of all available USDT perpetual futures symbols.
  - `process_symbol()`: Fetches the daily k-line (candlestick) data for a single symbol and calculates the percentage price change from the previous day's close. It includes retry logic with exponential backoff to handle API rate limits.
  - `get_perpetual_futures_daily_data()`: Concurrently fetches data for all symbols using a `ThreadPoolExecutor`.

- **Background Process (`src/strengther/background_process.py`):** A background task that runs in a continuous loop. It calls `get_perpetual_futures_daily_data()` to get fresh data, converts it to a pandas DataFrame, and then updates the `data_store` in `src/strengther/api.py` by calling `update_data()`.

- **Data Models (`src/strengther/models.py`):** Defines the Pydantic models used for data validation and serialization, primarily `SymbolChangeData`.

## Data Flow

1.  On application startup, `app.py` calls `update_symbols()` to populate the list of symbols to track.
2.  `app.py` starts the `background_task()` from `background_process.py`.
3.  The `background_task` periodically (every 15 seconds) calls `get_perpetual_futures_daily_data()` in `main.py`.
4.  `main.py` fetches the latest k-line data for all symbols from the Bybit API.
5.  The fetched data is processed and returned to `background_process.py`.
6.  `background_process.py` calls the `update_data()` function in `api.py` to refresh the in-memory `data_store`.
7.  The FastAPI endpoints in `api.py` serve the latest data from the `data_store`.

## Developer Workflow

### Setup

Install dependencies using Poetry:

```bash
uv sync
```

### Running the Application

To run the FastAPI server:

```bash
uv run strengther
```

The application will be available at `http://0.0.0.0:8003`.

### Key Files to Reference

- `src/strengther/app.py`: For application startup logic and background task management.
- `src/strengther/api.py`: For adding or modifying API endpoints.
- `src/strengther/main.py`: For changes to the Bybit data fetching and processing logic.
- `src/strengther/background_process.py`: For adjusting the data refresh interval or logic.
- `pyproject.toml`: For managing project dependencies.

### Instructions for AI Coding Agents

Keep responses concise and focused on the specific task at hand. Provide clear, actionable code snippets that can be directly integrated into the existing codebase. Avoid unnecessary complexity and ensure that any new code adheres to the existing coding standards and practices used in the Strengther project.

Attempt to format responses in a way that is easy to read and understand, using appropriate comments and documentation where necessary. Ensure that any new functionality is well-tested and integrates seamlessly with the existing codebase.
