"""Assessment Routes"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Assessment, Course, User, UserRole
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


class AssessmentCreate(BaseModel):
    course_id: int
    title: str
    description: str
    passing_score: float = 70.0
    time_limit_minutes: Optional[int] = None


class AssessmentResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: str
    passing_score: float
    time_limit_minutes: Optional[int] = None


@router.get("/course/{course_id}", response_model=List[AssessmentResponse])
async def list_course_assessments(course_id: int, db: AsyncSession = Depends(get_db)):
    """List all assessments for a course"""
    result = await db.execute(select(Assessment).where(Assessment.course_id == course_id))
    assessments = result.scalars().all()

    return [
        AssessmentResponse(
            id=assessment.id,
            course_id=assessment.course_id,
            title=assessment.title,
            description=assessment.description,
            passing_score=assessment.passing_score,
            time_limit_minutes=assessment.time_limit_minutes,
        )
        for assessment in assessments
    ]


@router.post("/", response_model=AssessmentResponse)
async def create_assessment(
    data: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new assessment"""
    if current_user.role not in [UserRole.ADMIN, UserRole.INSTRUCTOR]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Instructor or admin role required")

    result = await db.execute(select(Course).where(Course.id == data.course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if current_user.role == UserRole.INSTRUCTOR and course.instructor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create assessment for this course")

    assessment = Assessment(
        course_id=data.course_id,
        title=data.title,
        description=data.description,
        passing_score=data.passing_score,
        time_limit_minutes=data.time_limit_minutes,
    )

    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)

    return AssessmentResponse(
        id=assessment.id,
        course_id=assessment.course_id,
        title=assessment.title,
        description=assessment.description,
        passing_score=assessment.passing_score,
        time_limit_minutes=assessment.time_limit_minutes,
    )


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(assessment_id: int, db: AsyncSession = Depends(get_db)):
    """Get specific assessment details"""
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    return AssessmentResponse(
        id=assessment.id,
        course_id=assessment.course_id,
        title=assessment.title,
        description=assessment.description,
        passing_score=assessment.passing_score,
        time_limit_minutes=assessment.time_limit_minutes,
    )


@router.post("/{assessment_id}/submit")
async def submit_assessment(
    assessment_id: int,
    answers: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit assessment answers"""
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    if not answers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Answers payload is required")

    return {
        "success": True,
        "message": "Assessment submission received. Assessment scoring and response analysis are in development.",
        "assessment_id": assessment.id,
        "submitted_by": current_user.id,
        "answers_received": len(answers),
    }


@router.get("/{assessment_id}/results/{user_id}")
async def get_assessment_results(
    assessment_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get student's assessment results"""
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    return {
        "success": True,
        "assessment_id": assessment.id,
        "user_id": user_id,
        "score": 0.0,
        "status": "pending",
        "message": "Assessment result reporting is under development.",
    }
