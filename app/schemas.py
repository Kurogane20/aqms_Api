from datetime import datetime, timezone
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field
from .config import settings

# ==== Helpers ====
def to_aware(ts: Union[int, float, str, datetime]) -> datetime:
    if isinstance(ts, datetime):
        return ts.astimezone(timezone.utc) if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    if isinstance(ts, (int, float)):
        if ts > 10_000_000_000:
            ts = ts / 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            if ts.isdigit():
                return to_aware(int(ts))
            raise
    raise ValueError("Unsupported datetime format")

# ==== Sensor ====
class SensorPoint(BaseModel):
    uid: str = Field(..., max_length=64)
    datetime: Union[int, float, str, datetime]
    co: Optional[float] = None
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    tvoc: Optional[float] = None
    o3: Optional[float] = None
    so2: Optional[float] = None
    no: Optional[float] = None
    no2: Optional[float] = None    
    rh: Optional[float] = None
    noise: Optional[float] = None
    windDir: Optional[float] = None
    windSpeed: Optional[float] = None
    temp: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_txt: Optional[str] = None

    

    def to_row(self) -> dict:
        return {
            "uid": self.uid,
            "ts": to_aware(self.datetime),
            "co": self.co,
            "pm25": self.pm25,
            "pm10": self.pm10,
            "tvoc": self.tvoc,
            "o3": self.o3,
            "so2": self.so2,
            "no": self.no,
            "no2": self.no2,
            "rh": self.rh,
            "noise": self.noise,
            "windDir": self.windDir,
            "windSpeed": self.windSpeed,
            "temp": self.temp,
            "wind_speed_kmh": self.wind_speed_kmh,
            "wind_txt": self.wind_txt,
        }

class IngestBody(BaseModel):
    data: Union[SensorPoint, List[SensorPoint]]

class SensorFlat(BaseModel):
    uid: str
    ts: datetime
    co: float | None = None
    pm25: float | None = None
    pm10: float | None = None
    tvoc: float | None = None
    o3: float | None = None
    so2: float | None = None
    no: float | None = None
    no2: float | None = None
    temp: float | None = None
    humidity: float | None = None
    wind_speed_kmh: float | None = None 
    wind_txt: str | None = None
    noise: float | None = None

# ==== Maintenance ====
class MaintenanceCreate(BaseModel):
    uid: str = Field(..., max_length=64)
    title: str | None = None
    technician: str = Field(..., max_length=128)
    description: str = Field(..., min_length=3)
    performed_at: datetime | int | float | str | None = None
    meta: dict | None = None

class MaintenanceOut(BaseModel):
    id: int
    uid: str
    title: str | None = None
    technician: str
    description: str
    performed_at: datetime
    meta: dict | None

class PageMeta(BaseModel):
    page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PageOut(BaseModel):
    meta: PageMeta
    items: list[MaintenanceOut]

    # ==== Sensor (paginate) ====
class SensorOut(BaseModel):
    id: int
    uid: str
    ts: datetime
    co: float | None = None
    pm25: float | None = None
    pm10: float | None = None
    tvoc: float | None = None
    o3: float | None = None
    so2: float | None = None
    no: float | None = None
    no2: float | None = None
    temp: float | None = None
    rh: float | None = None
    wind_speed_kmh: float | None = None
    wind_txt: str | None = None
    noise: float | None = None
    
    # kalau mau lihat payload asli, aktifkan kolom ini & endpoint diubah untuk include raw
    # raw: dict | None = None

class PageOutSensors(BaseModel):
    meta: PageMeta
    items: list[SensorOut]

