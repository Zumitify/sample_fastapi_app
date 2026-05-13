import os
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import Application, Assignment, User
from ..schemas import AssignmentCreate, AssignmentOut


router = APIRouter(prefix="/assignments", tags=["assignments"])

os.makedirs(settings.upload_dir, exist_ok=True)


@router.post("/{application_id}", response_model=AssignmentOut)
async def create_assignment(
    application_id: int,
    payload: AssignmentCreate,
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

    assignment = Assignment(
        application_id=application_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
    )
    db.add(assignment)
    db.commit()
    await db.refresh(assignment)
    return assignment


@router.post("/{assignment_id}/upload", response_model=AssignmentOut)
async def upload_assignment_file(
    assignment_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Assignment)
        .join(Application, Assignment.application_id == Application.id)
        .where(
            Assignment.id == assignment_id,
            Application.user_id == current_user.id,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    file_path = os.path.join(settings.upload_dir, f"{assignment_id}_{file.filename}")
    with open(file_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    assignment.file_path = file_path
    await db.commit()
    await db.refresh(assignment)
    return assignment


@router.get("/", response_model=list[AssignmentOut])
async def list_assignments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Assignment)
        .join(Application, Assignment.application_id == Application.id)
        .where(Application.user_id == current_user.id)
        .order_by(Assignment.due_date.asc())
    )
    return result.scalars().all()


@router.patch("/{assignment_id}/complete", response_model=AssignmentOut)
async def mark_complete(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Assignment)
        .join(Application, Assignment.application_id == Application.id)
        .where(
            Assignment.id == assignment_id,
            Application.user_id == current_user.id,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment.completed = True
    await db.commit()
    await db.refresh(assignment)
    return assignment
