from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import MaintenanceHistory
from ..schemas import MaintenanceCreate, MaintenanceOut, PageOut
from ..utils.pagination import paginate_meta

router = APIRouter(prefix="/maintenance", tags=["maintenance"])

@router.post("", response_model=MaintenanceOut)
async def create_maintenance(payload: MaintenanceCreate, db: AsyncSession = Depends(get_db)):
    try:
        performed_at = payload.performed_at
        if performed_at is None:
            performed_at = datetime.now(timezone.utc)

        elif isinstance(performed_at, (int, float)):
            if performed_at > 10_000_000_000:
                performed_at = performed_at / 1000.0
            performed_at = datetime.fromtimestamp(performed_at, tz=timezone.utc)

        elif isinstance(performed_at, str):
            try:
                performed_at = datetime.fromisoformat(performed_at.replace("Z", "+00:00"))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid performed_at: {e}")

        rec = MaintenanceHistory(
            uid=payload.uid,
            title=payload.title,
            technician=payload.technician,
            description=payload.description,
            performed_at=performed_at,
            meta=payload.meta or None,
        )
        db.add(rec)
        await db.commit()
        await db.refresh(rec)
        return MaintenanceOut(
            id=rec.id,
            uid=rec.uid,
            title=rec.title,
            technician=rec.technician,
            description=rec.description,
            performed_at=rec.performed_at,
            meta=rec.meta,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=PageOut)
async def list_maintenance(
    db: AsyncSession = Depends(get_db),
    uid: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=200),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
):
    try:
        # Base query
        stmt = select(MaintenanceHistory)
        cnt_stmt = select(func.count(MaintenanceHistory.id))

        # Filters
        if uid:
            stmt = stmt.where(MaintenanceHistory.uid == uid)
            cnt_stmt = cnt_stmt.where(MaintenanceHistory.uid == uid)

        if date_from:
            stmt = stmt.where(MaintenanceHistory.performed_at >= date_from)
            cnt_stmt = cnt_stmt.where(MaintenanceHistory.performed_at >= date_from)
        if date_to:
            stmt = stmt.where(MaintenanceHistory.performed_at < date_to)
            cnt_stmt = cnt_stmt.where(MaintenanceHistory.performed_at < date_to)

        # Count
        total = (await db.execute(cnt_stmt)).scalar_one()

        # Pagination
        meta = paginate_meta(page, per_page, total)
        offset = (meta["page"] - 1) * per_page

        # Data
        rows = (await db.execute(
            stmt.order_by(desc(MaintenanceHistory.performed_at))
                .offset(offset)
                .limit(per_page)
        )).scalars().all()

        items = [
            MaintenanceOut(
                id=r.id,
                uid=r.uid,
                title=r.title,
                technician=r.technician,
                description=r.description,
                performed_at=r.performed_at,
                meta=r.meta,
            ) for r in rows
        ]

        return {"meta": meta, "items": items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
