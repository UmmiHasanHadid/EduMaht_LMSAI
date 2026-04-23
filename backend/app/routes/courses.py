"""Course Routes"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Course, UserRole
from app.utils.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/courses", tags=["courses"])


class CourseCreate(BaseModel):
    title: str
    description: str
    category: str
    level: str
    is_published: Optional[bool] = False


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    is_published: Optional[bool] = None


class CourseResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    level: str
    rating: float
    is_published: bool


@router.get("/", response_model=List[CourseResponse])
async def list_courses(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all published courses"""
    query = select(Course).where(Course.is_published == True)

    if category:
        query = query.where(Course.category == category)

    if search:
        ilike_pattern = f"%{search}%"
        query = query.where(
            or_(Course.title.ilike(ilike_pattern), Course.description.ilike(ilike_pattern))
        )

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    courses = result.scalars().all()

    return [
        CourseResponse(
            id=course.id,
            title=course.title,
            description=course.description,
            category=course.category,
            level=course.level,
            rating=course.rating or 0.0,
            is_published=course.is_published,
        )
        for course in courses
    ]


@router.post("/", response_model=CourseResponse)
async def create_course(
    data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new course (instructor/admin only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.INSTRUCTOR]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Instructor or admin role required")

    course = Course(
        title=data.title,
        description=data.description,
        category=data.category,
        level=data.level,
        is_published=data.is_published,
        instructor_id=current_user.id,
    )

    db.add(course)
    await db.commit()
    await db.refresh(course)

    return CourseResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        category=course.category,
        level=course.level,
        rating=course.rating or 0.0,
        is_published=course.is_published,
    )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    """Get specific course details"""
    result = await db.execute(select(Course).where(Course.id == course_id, Course.is_published == True))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    return CourseResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        category=course.category,
        level=course.level,
        rating=course.rating or 0.0,
        is_published=course.is_published,
    )


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    data: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update course (instructor/admin only)"""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    if current_user.role == UserRole.INSTRUCTOR and course.instructor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this course")

    if data.title is not None:
        course.title = data.title
    if data.description is not None:
        course.description = data.description
    if data.category is not None:
        course.category = data.category
    if data.level is not None:
        course.level = data.level
    if data.is_published is not None:
        course.is_published = data.is_published

    db.add(course)
    await db.commit()
    await db.refresh(course)

    return CourseResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        category=course.category,
        level=course.level,
        rating=course.rating or 0.0,
        is_published=course.is_published,
    )


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete course (instructor/admin only)"""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    if current_user.role == UserRole.INSTRUCTOR and course.instructor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this course")

    await db.delete(course)
    await db.commit()

    return {"message": "Course deleted successfully"}
