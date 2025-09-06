import asyncio
import json
import logging
from contextlib import asynccontextmanager

from asyncio_mqtt import Client as AsyncMQTTClient, MqttError

from .config import settings
from .database import SessionLocal
from .models import SensorData
from .email_sender import send_notification_email

logger = logging.getLogger(__name__)

async def process_mqtt_message(topic: str, payload: bytes):
    try:
        data = json.loads(payload.decode())
        # Assumindo tópicos como "esp32/sensors/motion" ou "esp32/sensors/sound"
        parts = topic.split('/')
        if len(parts) < 3 or parts[1] != "sensors":
            logger.warning(f"MQTT topic format not recognized: {topic}")
            return
        sensor_type = parts[-1]

        # Validar dados básicos
        if "value" not in data:
            logger.warning(f"Payload missing 'value' key on topic {topic}: {data}")
            return

        new_data = SensorData(
            sensor_type=sensor_type,
            value=data["value"],
            # Você pode enviar o timestamp do ESP32 ou deixar o DB gerar
            # timestamp=data.get("timestamp") # Se o ESP32 envia
        )

        with SessionLocal() as db:
            db.add(new_data)
            db.commit()
            db.refresh(new_data)
            logger.info(f"Dados do sensor armazenados: {new_data.sensor_type} - {new_data.value}")

            # Lógica para enviar alertas por e-mail
            if sensor_type == "motion" and data["value"] == 1: # Assumindo 1 para movimento detectado
                subject = "Alerta de Movimento Detectado!"
                body = f"Movimento detectado no ESP32 em {new_data.timestamp}."
                await send_notification_email(subject, body, settings.ALERT_EMAIL_RECIPIENT)
                logger.warning(f"Email de alerta de movimento enviado para {settings.ALERT_EMAIL_RECIPIENT}")
            elif sensor_type == "sound" and data["value"] > settings.SOUND_THRESHOLD:
                subject = "Alerta de Som Elevado Detectado!"
                body = f"Nível de som elevado ({data['value']}) detectado no ESP32 em {new_data.timestamp}."
                await send_notification_email(subject, body, settings.ALERT_EMAIL_RECIPIENT)
                logger.warning(f"Email de alerta de som enviado para {settings.ALERT_EMAIL_RECIPIENT}")

    except json.JSONDecodeError as e:
        logger.error(f"Falha ao decodificar JSON da mensagem MQTT no tópico {topic}: {e}")
    except Exception as e:
        logger.error(f"Erro ao processar mensagem MQTT: {e}", exc_info=True)


async def mqtt_subscriber_task():
    logger.info("Iniciando tarefa de subscrição MQTT...")
    retries = 0
    while True:
        try:
            # Configuração de autenticação (se houver)
            mqtt_kwargs = {
                "hostname": settings.MQTT_BROKER_HOST,
                "port": settings.MQTT_BROKER_PORT,
                "tls_params": None # Desativar TLS por padrão se a porta for 1883
            }
            if settings.MQTT_BROKER_USER and settings.MQTT_BROKER_PASSWORD:
                mqtt_kwargs["username"] = settings.MQTT_BROKER_USER
                mqtt_kwargs["password"] = settings.MQTT_BROKER_PASSWORD
            
            # Se usar porta padrão TLS para MQTT (8883), ative tls_params
            if settings.MQTT_BROKER_PORT == 8883:
                import ssl
                mqtt_kwargs["tls_params"] = AsyncMQTTClient.TLSParameters(
                    # cert_reqs=ssl.CERT_REQUIRED, # Pode ser necessário para brokers públicos
                    # tls_version=ssl.PROTOCOL_TLSv1_2 # Especificar versão TLS
                )

            async with AsyncMQTTClient(**mqtt_kwargs) as client:
                logger.info(f"Conectado ao broker MQTT: {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
                await client.subscribe("esp32/sensors/#") # Subscreve a todos os tópicos sob "esp32/sensors/"
                logger.info("Subscrito ao tópico 'esp32/sensors/#'")

                async for message in client.messages:
                    await process_mqtt_message(message.topic, message.payload)
                
        except MqttError as error:
            logger.error(f"Erro MQTT: {error}. Reconectando em 5 segundos...", exc_info=True)
            retries += 1
            await asyncio.sleep(min(5 * (2 ** retries), 60)) # Backoff exponencial
        except Exception as e:
            logger.error(f"Erro inesperado na tarefa do subscritor MQTT: {e}. Reiniciando em 5 segundos...", exc_info=True)
            retries += 1
            await asyncio.sleep(min(5 * (2 ** retries), 60))

@asynccontextmanager
async def mqtt_lifespan(app):
    # Startup
    logger.info("Aplicação FastAPI iniciando. Iniciando subscritor MQTT...")
    task = asyncio.create_task(mqtt_subscriber_task())
    yield
    # Shutdown
    logger.info("Aplicação FastAPI encerrando. Cancelando subscritor MQTT...")
    task.cancel()
    try:
        await task # Aguarda o cancelamento para garantir a limpeza
    except asyncio.CancelledError:
        logger.info("Tarefa do subscritor MQTT cancelada.")