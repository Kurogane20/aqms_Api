import asyncio
import json
import os
import ssl
from typing import Optional, List

from asyncio_mqtt import Client, MqttError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .config import settings
from .db import SessionLocal
from .models import SensorData
from .schemas import SensorPoint

class MQTTWorker:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._stopping = asyncio.Event()

    async def start(self):
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._runner())

    async def stop(self):
        self._stopping.set()
        if self._task:
            await asyncio.wait([self._task], timeout=5)

    async def _runner(self):
        backoff = 1
        while not self._stopping.is_set():
            try:
                mode = settings.MQTT_MODE.lower()
                tls = ssl.create_default_context()

                print(f"[MQTT] Connecting to {settings.MQTT_HOST}:{settings.MQTT_PORT} "
                      f"mode={mode} user={settings.MQTT_USER} topic={settings.MQTT_TOPIC}")

                if mode == "tls":
                    async with Client(
                        hostname=settings.MQTT_HOST,
                        port=settings.MQTT_PORT,
                        username=settings.MQTT_USER or None,
                        password=settings.MQTT_PASS or None,
                        client_id=f"fastapi-mqtt-{os.getpid()}",
                        clean_session=True,
                        keepalive=60,
                        tls_context=tls,
                    ) as client:
                        await self._listen(client)

                elif mode == "wss":
                    async with Client(
                        hostname=settings.MQTT_HOST,
                        port=settings.MQTT_PORT,
                        username=settings.MQTT_USER or None,
                        password=settings.MQTT_PASS or None,
                        client_id=f"fastapi-mqtt-{os.getpid()}",
                        clean_session=True,
                        keepalive=60,
                        tls_context=tls,
                        transport="websockets",
                        websocket_path="/mqtt"
                    ) as client:
                        await self._listen(client)

                else:
                    # TCP plain (1883)
                    async with Client(
                        hostname=settings.MQTT_HOST,
                        port=settings.MQTT_PORT,
                        username=settings.MQTT_USER or None,
                        password=settings.MQTT_PASS or None,
                        client_id=f"fastapi-mqtt-{os.getpid()}",
                        clean_session=True,
                        keepalive=60,
                    ) as client:
                        await self._listen(client)

                backoff = 1  # reset ketika sukses

            except MqttError as e:
                print(f"[MQTT] Disconnected: {e}. Reconnecting in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
            except Exception as e:
                print(f"[MQTT] Error: {e}")
                await asyncio.sleep(3)

    async def _listen(self, client: Client):
        await client.subscribe(settings.MQTT_TOPIC)
        print(f"[MQTT] Connected → Subscribed: {settings.MQTT_TOPIC}")

        async with client.unfiltered_messages() as messages:
            async for message in messages:
                if self._stopping.is_set():
                    break
                await self._handle_message(message.topic, message.payload)

    async def _handle_message(self, topic: str, payload: bytes):
        try:
            text = payload.decode("utf-8", errors="replace").strip()
            if not text:
                return

            try:
                body = json.loads(text)
            except json.JSONDecodeError:
                if settings.APP_DEBUG:
                    print(f"[MQTT] Skip non-JSON on {topic}: {payload[:80]!r}")
                return

            try:
                parts = topic.split("/")
                uid_from_topic = parts[1] if len(parts) >= 2 else None
            except Exception:
                uid_from_topic = None

            def normalize_one(obj: dict) -> dict:
                if "uid" not in obj and uid_from_topic:
                    obj["uid"] = uid_from_topic
                if "datetime" not in obj:
                    for k in ("ts", "time", "t"):
                        if k in obj:
                            obj["datetime"] = obj[k]
                            break
                return obj

            rows: List[SensorPoint] = []
            if isinstance(body, dict):
                body = normalize_one(body)
                sp_kwargs = {k: body.get(k) for k in ("uid", "datetime", "co", "pm25", "pm10", "tvoc", "o3", "so2", "no", "no2", "temp", "rh", "wind_speed_kmh", "wind_txt", "noise")}
                rows.append(SensorPoint(**sp_kwargs))
                raw_for_db = body
            elif isinstance(body, list):
                raw_for_db = []
                for item in body:
                    if not isinstance(item, dict):
                        raise ValueError("Array elements must be JSON objects")
                    item = normalize_one(item)
                    sp_kwargs = {k: item.get(k) for k in ("uid", "datetime", "co", "pm25", "pm10", "tvoc", "o3", "so2", "no", "no2", "temp", "rh", "wind_speed_kmh", "wind_txt", "noise")}
                    rows.append(SensorPoint(**sp_kwargs))
                    raw_for_db.append(item)
            else:
                raise ValueError("Unsupported JSON format")

            async with SessionLocal() as session:
                to_add = []
                for i, p in enumerate(rows):
                    raw_item = raw_for_db[i] if isinstance(raw_for_db, list) else raw_for_db
                    rec = SensorData(**p.to_row(), raw=json.loads(json.dumps(raw_item)))
                    to_add.append(rec)
                session.add_all(to_add)
                await session.commit()

            if settings.APP_DEBUG:
                print(f"[MQTT] {topic} → stored {len(rows)} row(s)")

        except Exception as e:
            print(f"[MQTT] Handler error: {e}")
