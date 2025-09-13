from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text, select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..schemas import IngestBody, SensorPoint, SensorFlat, SensorOut, PageOutSensors
from ..utils.pagination import paginate_meta
from ..models import SensorData
from datetime import datetime

router = APIRouter(prefix="/data", tags=["sensors"])

@router.get("/latest/flat", response_model=SensorFlat | dict)
async def latest_flat(uid: str | None = None, db: AsyncSession = Depends(get_db)):
    q = text("""
        SELECT uid, ts, co, pm25, pm10, tvoc, so2, o3, no, no2, rh, temp, wind_speed_kmh, wind_txt, noise
        FROM sensor_data
        WHERE (:uid IS NULL OR uid = :uid)
        ORDER BY ts DESC
        LIMIT 1
    """)
    row = (await db.execute(q, {"uid": uid})).mappings().first()
    if not row:
        return {}
    r = dict(row)
    return SensorFlat(
        uid=r["uid"],
        ts=r["ts"],
        co=r["co"],
        pm25=r["pm25"],
        pm10=r["pm10"],
        tvoc=r["tvoc"],
        o3=r["o3"],
        so2=r["so2"],
        no=r["no"],
        no2=r["no2"],
        rh=r["rh"],
        humidity=r["rh"],
        wind_speed_kmh=r["wind_speed_kmh"],
        wind_txt=r["wind_txt"],
        noise=r["noise"],
    )

@router.get("", response_model=PageOutSensors)
async def list_data(
    db: AsyncSession = Depends(get_db),
    uid: str | None = None,
    page: int = 1,
    per_page: int = 50,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    order: str = "desc",  # "desc" atau "asc"
):
    """
    List data sensor dengan pagination.
    Filter: uid, rentang tanggal (UTC), urutan ts.
    """
    # Base statement
    stmt = select(SensorData)
    cnt = select(func.count(SensorData.id))

    # Filters
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

    # Pagination meta
    per_page = max(1, min(per_page, 500))
    meta = paginate_meta(page, per_page, total)
    offset = (meta["page"] - 1) * per_page

    # Order
    order_by = desc(SensorData.ts) if order.lower() != "asc" else SensorData.ts

    rows = (await db.execute(
        stmt.order_by(order_by).offset(offset).limit(per_page)
    )).scalars().all()

    items = [
        SensorOut(
            id=r.id,
            uid=r.uid,
            ts=r.ts,
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

            # raw=r.raw,  # aktifkan kalau butuh payload mentah
        )
        for r in rows
    ]
    return {"meta": meta, "items": items}


@router.post("/ingest")
async def ingest(body: IngestBody, db: AsyncSession = Depends(get_db)):
    try:
        points = [body.data] if isinstance(body.data, SensorPoint) else body.data
        to_add = [
            SensorData(**p.to_row())
            for p in points
        ]
        db.add_all(to_add)
        await db.commit()
        return {"stored": len(to_add)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
