"""Enrollment Routes"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Enrollment, Course, User, UserRole, EnrollmentStatus
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/enrollments", tags=["enrollments"])


class EnrollmentCreate(BaseModel):
    course_id: int


class EnrollmentUpdate(BaseModel):
    progress: Optional[float] = None
    status: Optional[EnrollmentStatus] = None


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    status: str
    progress: float
    score: float


@router.post("/", response_model=EnrollmentResponse)
async def enroll_in_course(
    data: EnrollmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enroll student in a course"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can enroll in courses")

    result = await db.execute(select(Course).where(Course.id == data.course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.course_id == data.course_id,
            Enrollment.student_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already enrolled in this course")

    enrollment = Enrollment(
        student_id=current_user.id,
        course_id=data.course_id,
        status=EnrollmentStatus.ACTIVE,
    )

    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)

    return EnrollmentResponse(
        id=enrollment.id,
        student_id=enrollment.student_id,
        course_id=enrollment.course_id,
        status=enrollment.status.value,
        progress=enrollment.progress,
        score=enrollment.score,
    )


@router.get("/my-courses", response_model=List[EnrollmentResponse])
async def get_my_enrollments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's course enrollments"""
    result = await db.execute(select(Enrollment).where(Enrollment.student_id == current_user.id))
    enrollments = result.scalars().all()

    return [
        EnrollmentResponse(
            id=enrollment.id,
            student_id=enrollment.student_id,
            course_id=enrollment.course_id,
            status=enrollment.status.value,
            progress=enrollment.progress,
            score=enrollment.score,
        )
        for enrollment in enrollments
    ]


@router.get("/{enrollment_id}", response_model=EnrollmentResponse)
async def get_enrollment(
    enrollment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific enrollment details"""
    result = await db.execute(select(Enrollment).where(Enrollment.id == enrollment_id))
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    if current_user.role == UserRole.STUDENT and enrollment.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this enrollment")

    return EnrollmentResponse(
        id=enrollment.id,
        student_id=enrollment.student_id,
        course_id=enrollment.course_id,
        status=enrollment.status.value,
        progress=enrollment.progress,
        score=enrollment.score,
    )


@router.put("/{enrollment_id}")
async def update_enrollment_progress(
    enrollment_id: int,
    data: EnrollmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update enrollment progress"""
    result = await db.execute(select(Enrollment).where(Enrollment.id == enrollment_id))
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    if current_user.role == UserRole.STUDENT and enrollment.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this enrollment")

    if data.progress is not None:
        enrollment.progress = max(0.0, min(100.0, data.progress))
        if enrollment.progress >= 100.0:
            enrollment.status = EnrollmentStatus.COMPLETED

    if data.status is not None:
        enrollment.status = data.status

    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)

    return {
        "message": "Enrollment updated successfully",
        "enrollment": {
            "id": enrollment.id,
            "student_id": enrollment.student_id,
            "course_id": enrollment.course_id,
            "status": enrollment.status.value,
            "progress": enrollment.progress,
            "score": enrollment.score,
        },
    }


@router.delete("/{enrollment_id}")
async def unenroll_from_course(
    enrollment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unenroll student from course"""
    result = await db.execute(select(Enrollment).where(Enrollment.id == enrollment_id))
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    if current_user.role == UserRole.STUDENT and enrollment.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to unenroll")

    await db.delete(enrollment)
    await db.commit()

    return {"message": "Enrollment cancelled successfully"}
