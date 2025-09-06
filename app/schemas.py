from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SensorDataCreate(BaseModel):
    sensor_type: str
    value: float
    timestamp: Optional[datetime] = None # Opcional se o DB gerar

class SensorDataRead(BaseModel):
    id: int
    sensor_type: str
    value: float
    timestamp: datetime

    class Config:
        from_attributes = True # updated from orm_mode = True for Pydantic v2