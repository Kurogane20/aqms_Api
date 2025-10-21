from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text, select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..schemas import IngestBody, SensorPoint, SensorFlat, SensorOut, PageOutSensors
from ..utils.pagination import paginate_meta
from ..models import SensorData
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import random

JAKARTA = ZoneInfo("Asia/Jakarta")

router = APIRouter(prefix="/data", tags=["sensors"])

@router.get("/latest/flat", response_model=SensorFlat | dict)
async def latest_flat(uid: str | None = None, db: AsyncSession = Depends(get_db)):
    q = text("""
        SELECT uid, ts, co, pm25, pm10, tvoc, so2, o3, no, no2, rh, temp, wind_speed_kmh, wind_txt, noise, voltage, current, co2
        FROM sensor_data
        WHERE (:uid IS NULL OR uid = :uid)
        ORDER BY ts DESC
        LIMIT 1
    """)
    row = (await db.execute(q, {"uid": uid})).mappings().first()
    if not row:
        return {}
    r = dict(row)
    ts_utc = r["ts"]
    if ts_utc.tzinfo is None:  # database biasanya naive
        ts_utc = ts_utc.replace(tzinfo=timezone.utc)
    ts_local = ts_utc.astimezone(ZoneInfo("Asia/Jakarta"))

    return SensorFlat(
        uid=r["uid"],
        ts=ts_local.isoformat(),
        co=r["co"],
        pm25=r["pm25"],
        pm10=r["pm10"],
        tvoc=r["tvoc"],
        o3=r["o3"],
        so2=r["so2"],
        no=r["no"],
        no2=r["no2"],
        rh=r["rh"],
        temp=r["temp"],
        humidity=r["rh"],
        wind_speed_kmh=r["wind_speed_kmh"],
        wind_txt=r["wind_txt"],
        noise=r["noise"],
        voltage=r["voltage"],
        current=r["current"],
        co2=r["co2"],
    )

@router.get("", response_model=PageOutSensors)
async def list_data(
    db: AsyncSession = Depends(get_db),
    uid: str | None = None,
    page: int = 1,
    per_page: int = 50,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    order: str = "desc",
):
    stmt = select(SensorData)
    cnt = select(func.count(SensorData.id))

    if uid:
        stmt = stmt.where(SensorData.uid == uid)
        cnt = cnt.where(SensorData.uid == uid)

    if date_from:
        stmt = stmt.where(SensorData.ts >= date_from)
        cnt = cnt.where(SensorData.ts >= date_from)
    if date_to:
        stmt = stmt.where(SensorData.ts < date_to)
        cnt = cnt.where(SensorData.ts < date_to)

    total = (await db.execute(cnt)).scalar_one()

    per_page = max(1, min(per_page, 500))
    meta = paginate_meta(page, per_page, total)
    offset = (meta["page"] - 1) * per_page

    order_by = desc(SensorData.ts) if order.lower() != "asc" else SensorData.ts

    rows = (
        await db.execute(
            stmt.order_by(order_by).offset(offset).limit(per_page)
        )
    ).scalars().all()

    items = []
    for r in rows:
        ts_utc = r.ts
        if ts_utc.tzinfo is None:
            ts_utc = ts_utc.replace(tzinfo=timezone.utc)
        ts_local = ts_utc.astimezone(JAKARTA)

        items.append(
            SensorOut(
                id=r.id,
                uid=r.uid,
                ts=ts_local.isoformat(),
                co=r.co,
                pm25=r.pm25,
                pm10=r.pm10,
                tvoc=r.tvoc,
                o3=r.o3,
                so2=r.so2,
                no=r.no,
                no2=r.no2,
                temp=r.temp,
                rh=r.rh,
                wind_speed_kmh=r.wind_speed_kmh,
                wind_txt=r.wind_txt,
                noise=r.noise,
                voltage=r.voltage,
                current=r.current,
                co2=r.co2,
            )
        )

    return {"meta": meta, "items": items}


@router.post("/ingest")
async def ingest(body: IngestBody, db: AsyncSession = Depends(get_db)):
    try:
        points = [body.data] if isinstance(body.data, SensorPoint) else body.data

        to_add = []
        for p in points:
            data = p.to_row()

            # --- jika tidak ada co2 dikirim, isi random antara 400–800 ppm ---
            if "co2" not in data or data["co2"] is None:
                data["co2"] = round(random.uniform(400.0, 800.0), 1)

            to_add.append(SensorData(**data))

        db.add_all(to_add)
        await db.commit()
        return {"stored": len(to_add), "co2_randomized": sum(1 for d in to_add if d.co2)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))