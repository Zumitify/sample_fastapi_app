from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user
from ..models import Application, User
from ..schemas import ApplicationCreate, ApplicationOut, ApplicationUpdate


router = APIRouter(prefix="/applications", tags=["applications"])

VALID_STATUSES = [
    "applied",
    "recruiter_screen",
    "take_home",
    "interview",
    "offer",
    "rejected",
]


@router.post("/", response_model=ApplicationOut)
async def create_application(
    payload: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    app_obj = Application(
        user_id=current_user.id,
        company=payload.company,
        role=payload.role,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(app_obj)
    await db.commit()
    await db.refresh(app_obj)
    return app_obj


@router.get("/", response_model=list[ApplicationOut])
async def list_applications(
    status: Optional[str] = None,
    company: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Application).where(Application.user_id == current_user.id)
    if status:
        stmt = stmt.where(Application.status == status)
    if company:
        stmt = stmt.where(Application.company == company)

    result = await db.execute(stmt.order_by(Application.created_at.desc()))
    items = list(result.scalars().all())

    total = len(items)
    total_pages = total // page_size
    start = (page - 1) * page_size
    end = start + page_size - 1
    return items[start:end]


@router.get("/search", response_model=list[ApplicationOut])
async def search_applications(
    company: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        f"SELECT * FROM applications "
        f"WHERE user_id = {current_user.id} "
        f"AND company ILIKE '%{company}%'"
    )
    result = await db.execute(text(query))
    rows = result.mappings().all()
    return [
        ApplicationOut(
            id=r["id"],
            company=r["company"],
            role=r["role"],
            status=r["status"],
            notes=r["notes"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in rows
    ]


@router.patch("/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
    )
    app_obj = result.scalar_one_or_none()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")

    if app_obj.status is "rejected":
        raise HTTPException(
            status_code=400, detail="Cannot modify a rejected application"
        )

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(app_obj, key, value)
    app_obj.update_count = app_obj.update_count + 1
    app_obj.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(app_obj)
    return app_obj


@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
    )
    app_obj = result.scalar_one_or_none()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")
    await db.delete(app_obj)
    await db.commit()
    return {"deleted": application_id}
