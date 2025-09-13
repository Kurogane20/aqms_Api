from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from .config import settings
from .db import init_db, engine
from .mqtt_worker import MQTTWorker
from .routers.sensors import router as sensors_router
from .routers.maintenance import router as maintenance_router

app = FastAPI(title="AQMS (CO/PM) MQTT → MySQL")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mqtt_worker = MQTTWorker()

from .config import settings
print("[CONF] MQTT_HOST=", settings.MQTT_HOST)
print("[CONF] MQTT_PORT=", settings.MQTT_PORT)
print("[CONF] MQTT_MODE=", settings.MQTT_MODE)
print("[CONF] MQTT_USER=", "(set)" if settings.MQTT_USER else "(none)")
print("[CONF] TOPIC    =", settings.MQTT_TOPIC)

@app.on_event("startup")
async def on_startup():
    await init_db()
    await mqtt_worker.start()
    # Debug route list
    print("[APP] Registered routes:")
    for r in app.routes:
        if isinstance(r, APIRoute):
            print("  -", r.path, r.methods)

@app.on_event("shutdown")
async def on_shutdown():
    await mqtt_worker.stop()
    await engine.dispose()

# Routers
app.include_router(sensors_router)
app.include_router(maintenance_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
