from fastapi import FastAPI, Depends, HTTPException
import uvicorn
import logging
from typing import List

from .config import settings
from .database import engine, Base, get_db
from .models import SensorData
from .schemas import SensorDataRead # Importar Schema
from .mqtt_client import mqtt_lifespan # Importar o lifespan do MQTT
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# O lifespan gerenciará a inicialização e desligamento da tarefa MQTT
app = FastAPI(lifespan=mqtt_lifespan)

@app.on_event("startup")
def startup_event():
    logger.info("Criando tabelas do banco de dados (se não existirem)...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tabelas do banco de dados criadas.")

@app.get("/")
async def read_root():
    return {"message": "FastAPI MQTT Sensor Listener is running!"}

@app.get("/sensor_data/", response_model=List[SensorDataRead])
async def get_sensor_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Endpoint para visualizar os dados recentes do sensor.
    """
    data = db.query(SensorData).offset(skip).limit(limit).all()
    return data

@app.get("/sensor_data/{data_id}", response_model=SensorDataRead)
async def get_single_sensor_data(data_id: int, db: Session = Depends(get_db)):
    """
    Endpoint para visualizar um dado de sensor específico.
    """
    data = db.query(SensorData).filter(SensorData.id == data_id).first()
    if data is None:
        raise HTTPException(status_code=404, detail="Sensor data not found")
    return data

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)