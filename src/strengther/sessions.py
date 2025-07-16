import logging
from time import time
from typing import Dict
from pydantic import BaseModel, Field

from strengther.models import SessionInfo

# For production, you would want a more robust logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

class SessionData(BaseModel):
    def __init__(self):

        self.sessions: Dict[str, SessionInfo] = {
            "tokyo": SessionInfo(
                start_time_utc=time(0, 0),  # 00:15 UTC (actual session starts 00:00, trading starts 00:15)
                name="Tokyo",
                duration_hours=8.75,  # Reduced by 0.25 hours (15 minutes)
            ),
            "london_winter": SessionInfo(
                start_time_utc=time(8, 0),  # 08:15 UTC (actual session starts 08:00, trading starts 08:15)
                name="London",
                duration_hours=8.75,  # Reduced by 0.25 hours (15 minutes)
            ),
            "london_summer": SessionInfo(
                start_time_utc=time(8, 0),  # 07:15 UTC (actual session starts 07:00, trading starts 07:15)
                name="London",
                duration_hours=8.75,  # Reduced by 0.25 hours (15 minutes)
            ),
            "new_york_winter": SessionInfo(
                start_time_utc=time(14, 30),  # 14:45 UTC (actual session starts 14:30, trading starts 14:45)
                name="New York",
                duration_hours=8.75,  # Reduced by 0.25 hours (15 minutes)
            ),
            "new_york_summer": SessionInfo(
                start_time_utc=time(13, 30),  # 13:45 UTC (actual session starts 13:30, trading starts 13:45)
                name="New York",
                duration_hours=8.75,  # Reduced by 0.25 hours (15 minutes)
            ),
        }