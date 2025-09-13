from datetime import datetime, timezone
from sqlalchemy import Integer, String, Float, DateTime, JSON, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class SensorData(Base):
    __tablename__ = "sensor_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    co: Mapped[float | None] = mapped_column(Float, nullable=True)
    no: Mapped[float | None] = mapped_column(Float, nullable=True)
    no2: Mapped[float | None] = mapped_column(Float, nullable=True)
    o3: Mapped[float | None] = mapped_column(Float, nullable=True)
    so2: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm25: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm10: Mapped[float | None] = mapped_column(Float, nullable=True)
    tvoc: Mapped[float | None] = mapped_column(Float, nullable=True)
    rh: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    temp: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    windSpeed: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    windDir: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    noise: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    wind_speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_txt: Mapped[str | None] = mapped_column(String(32), nullable=True)

Index("ix_sensor_uid_ts", SensorData.uid, SensorData.ts)

class MaintenanceHistory(Base):
    __tablename__ = "maintenance_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # alat/site
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc))
    technician: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
