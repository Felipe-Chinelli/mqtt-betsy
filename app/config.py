from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # MQTT
    MQTT_BROKER_HOST: str = "broker.hivemq.com"
    MQTT_BROKER_PORT: int = 1883
    MQTT_BROKER_USER: str = None
    MQTT_BROKER_PASSWORD: str = None

    # Database
    DATABASE_URL: str = "sqlite:///./sql_app.db"

    # Email
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    ALERT_EMAIL_RECIPIENT: str

    # Sensor Thresholds
    SOUND_THRESHOLD: float = 70.0 # Exemplo: dB

    # Logging
    LOG_LEVEL: str = "INFO"

settings = Settings()

# Configuração de logging
logging.basicConfig(level=settings.LOG_LEVEL.upper(),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')