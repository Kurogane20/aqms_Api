import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DB
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASS: str = "password"
    DB_NAME: str = "aqms"

    # MQTT
    MQTT_HOST: str = "broker.hivemq.com"
    MQTT_PORT: int = 1883
    MQTT_USER: str | None = None
    MQTT_PASS: str | None = None
    MQTT_TOPIC: str = "aqms/aqmsFOEmmEPISI01/#"
    MQTT_MODE: str = "tls"  # tcp, tls, wss

    # APP
    APP_DEBUG: bool = True
    CORS_ALLOW_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
