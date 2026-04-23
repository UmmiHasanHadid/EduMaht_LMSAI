"""
Attendance Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import Attendance, User, Course
from app.utils.auth import get_current_user
from pydantic import BaseModel
from datetime import datetime
from fastapi.responses import StreamingResponse
import io
from openpyxl import Workbook

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


class AttendanceCreate(BaseModel):
    student_id: int
    course_id: int
    lesson_id: int = None
    status: str = "present"
    notes: str = None


class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    lesson_id: int = None
    date: datetime
    status: str
    notes: str = None
    marked_by: int


@router.post("/", response_model=AttendanceResponse)
async def mark_attendance(
    attendance: AttendanceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark attendance for a student (Instructor only)"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if course belongs to instructor
    if current_user.role == "instructor":
        result = await db.execute(
            select(Course).where(Course.id == attendance.course_id, Course.instructor_id == current_user.id)
        )
        course = result.scalar_one_or_none()
        if not course:
            raise HTTPException(status_code=403, detail="Not authorized for this course")
    
    new_attendance = Attendance(
        student_id=attendance.student_id,
        course_id=attendance.course_id,
        lesson_id=attendance.lesson_id,
        status=attendance.status,
        notes=attendance.notes,
        marked_by=current_user.id
    )
    
    db.add(new_attendance)
    await db.commit()
    await db.refresh(new_attendance)
    
    return AttendanceResponse(
        id=new_attendance.id,
        student_id=new_attendance.student_id,
        course_id=new_attendance.course_id,
        lesson_id=new_attendance.lesson_id,
        date=new_attendance.date,
        status=new_attendance.status,
        notes=new_attendance.notes,
        marked_by=new_attendance.marked_by
    )


@router.get("/course/{course_id}/export")
async def export_course_attendance(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export attendance for a course as Excel (Instructor/Admin only)"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if current_user.role == "instructor":
        result = await db.execute(
            select(Course).where(Course.id == course_id, Course.instructor_id == current_user.id)
        )
        course = result.scalar_one_or_none()
        if not course:
            raise HTTPException(status_code=403, detail="Not authorized for this course")
    
    result = await db.execute(
        select(Attendance, User).join(User, Attendance.student_id == User.id).where(Attendance.course_id == course_id)
    )
    attendance_data = result.all()
    
    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"
    
    # Headers
    ws['A1'] = 'Student Name'
    ws['B1'] = 'Date'
    ws['C1'] = 'Status'
    ws['D1'] = 'Notes'
    
    # Data
    for row, (attendance, student) in enumerate(attendance_data, start=2):
        ws[f'A{row}'] = student.full_name
        ws[f'B{row}'] = attendance.date.strftime('%Y-%m-%d %H:%M')
        ws[f'C{row}'] = attendance.status
        ws[f'D{row}'] = attendance.notes or ''
    
    # Save to buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment; filename=attendance_course_{course_id}.xlsx"}
    )