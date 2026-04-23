"""Quiz Routes – system-generated AI quiz, teacher-uploaded, attempts, Excel export"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Course, Lesson, Quiz, QuizAttempt, User, UserRole
from app.utils.auth import get_current_user
from app.ai_services.gemini_tutor import ai_generate_quiz, ai_feedback_on_answer

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


# ---------------- Schemas ----------------
class QuizQuestion(BaseModel):
    id: int
    type: str = "multiple_choice"
    question: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: Optional[str] = ""
    points: int = 10


class QuizCreate(BaseModel):
    title: str
    description: str = ""
    course_id: Optional[int] = None
    topic: str = ""
    difficulty: str = "medium"
    time_limit_minutes: int = 30
    questions: List[QuizQuestion]


class QuizGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    num_questions: int = Field(8, ge=3, le=15)
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    course_id: Optional[int] = None
    lesson_id: Optional[int] = None
    question_types: Optional[List[str]] = None
    save_as_quiz: bool = False
    title: Optional[str] = None


class AttemptSubmit(BaseModel):
    answers: Dict[str, str]  # {"1": "A", "2": "jawaban bebas"}


# ---------------- Helpers ----------------
def _is_teacher(user: User) -> bool:
    return user.role in (UserRole.INSTRUCTOR, UserRole.ADMIN)


async def _load_material(db: AsyncSession, course_id: Optional[int], lesson_id: Optional[int]) -> str:
    chunks: List[str] = []
    if course_id:
        res = await db.execute(select(Course).where(Course.id == course_id))
        c = res.scalar_one_or_none()
        if c and c.description:
            chunks.append(c.description)
    if lesson_id:
        res = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
        l = res.scalar_one_or_none()
        if l:
            if l.content:
                chunks.append(l.content)
            elif l.description:
                chunks.append(l.description)
    return "\n\n".join(chunks)


def _serialize_quiz(q: Quiz, include_answers: bool) -> dict:
    qs = q.questions or []
    if not include_answers:
        cleaned = []
        for item in qs:
            item_copy = dict(item)
            item_copy.pop("correct_answer", None)
            item_copy.pop("explanation", None)
            cleaned.append(item_copy)
        qs = cleaned
    return {
        "id": q.id,
        "title": q.title,
        "description": q.description,
        "course_id": q.course_id,
        "source": q.source,
        "topic": q.topic,
        "difficulty": q.difficulty,
        "time_limit_minutes": q.time_limit_minutes,
        "teacher_id": q.teacher_id,
        "questions": qs,
        "question_count": len(q.questions or []),
        "created_at": q.created_at.isoformat() if q.created_at else None,
    }


# ---------------- Endpoints ----------------
@router.post("/generate")
async def generate_quiz(
    data: QuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Students & teachers can generate an AI practice quiz.
    - Students: always transient (not saved) — used for self-practice / struggle detection.
    - Teachers: may set save_as_quiz=True to persist as a course quiz.
    """
    material = await _load_material(db, data.course_id, data.lesson_id)
    try:
        generated = await ai_generate_quiz(
            topic=data.topic,
            num_questions=data.num_questions,
            difficulty=data.difficulty,
            material=material or None,
            question_types=data.question_types,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gagal generate quiz: {e}")

    if data.save_as_quiz and _is_teacher(current_user):
        quiz = Quiz(
            title=data.title or generated.get("title") or f"Quiz: {data.topic}",
            description=generated.get("description", ""),
            course_id=data.course_id,
            source="system",
            teacher_id=current_user.id,
            topic=data.topic,
            difficulty=data.difficulty,
            questions=generated.get("questions", []),
            time_limit_minutes=30,
        )
        db.add(quiz)
        await db.commit()
        await db.refresh(quiz)
        return {"saved": True, "quiz": _serialize_quiz(quiz, include_answers=True)}

    return {"saved": False, "preview": generated}


@router.post("/")
async def create_quiz(
    data: QuizCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Teacher uploads a manual quiz."""
    if not _is_teacher(current_user):
        raise HTTPException(status_code=403, detail="Hanya guru/admin yang boleh membuat kuis")

    quiz = Quiz(
        title=data.title,
        description=data.description,
        course_id=data.course_id,
        source="teacher",
        teacher_id=current_user.id,
        topic=data.topic,
        difficulty=data.difficulty,
        questions=[q.dict() for q in data.questions],
        time_limit_minutes=data.time_limit_minutes,
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    return _serialize_quiz(quiz, include_answers=True)


@router.get("/")
async def list_quizzes(
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Quiz)
    if course_id is not None:
        query = query.where(Quiz.course_id == course_id)
    res = await db.execute(query.order_by(Quiz.created_at.desc()))
    quizzes = res.scalars().all()
    include = _is_teacher(current_user)
    return [_serialize_quiz(q, include_answers=include) for q in quizzes]


@router.get("/{quiz_id}")
async def get_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = res.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Kuis tidak ditemukan")
    return _serialize_quiz(quiz, include_answers=_is_teacher(current_user))


@router.delete("/{quiz_id}")
async def delete_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not _is_teacher(current_user):
        raise HTTPException(status_code=403, detail="Hanya guru/admin")
    res = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = res.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Kuis tidak ditemukan")
    if current_user.role == UserRole.INSTRUCTOR and quiz.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Anda bukan pembuat kuis ini")
    await db.delete(quiz)
    await db.commit()
    return {"success": True}


@router.post("/{quiz_id}/attempts")
async def submit_attempt(
    quiz_id: int,
    data: AttemptSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = res.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Kuis tidak ditemukan")

    total = 0.0
    earned = 0.0
    per_question: List[Dict[str, Any]] = []
    for q in quiz.questions or []:
        qid = str(q.get("id"))
        pts = float(q.get("points", 10))
        total += pts
        user_ans = (data.answers.get(qid) or "").strip()
        correct = (q.get("correct_answer") or "").strip()
        is_correct = False
        if q.get("type") == "multiple_choice":
            is_correct = user_ans.lower() == correct.lower()
        else:
            # short_answer / essay: loose match — exact or correct fully contained
            if user_ans and correct:
                is_correct = (
                    user_ans.lower() == correct.lower()
                    or correct.lower() in user_ans.lower()
                )
        if is_correct:
            earned += pts
        per_question.append({
            "question_id": q.get("id"),
            "question": q.get("question"),
            "your_answer": user_ans,
            "correct_answer": correct,
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
            "points": pts,
        })

    percentage = (earned / total * 100.0) if total > 0 else 0.0

    attempt = QuizAttempt(
        quiz_id=quiz_id,
        student_id=current_user.id,
        answers=data.answers,
        score=earned,
        max_score=total,
        percentage=percentage,
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)

    return {
        "attempt_id": attempt.id,
        "score": earned,
        "max_score": total,
        "percentage": round(percentage, 2),
        "details": per_question,
    }


@router.get("/{quiz_id}/attempts")
async def list_attempts(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = res.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Kuis tidak ditemukan")

    query = select(QuizAttempt).where(QuizAttempt.quiz_id == quiz_id)
    if not _is_teacher(current_user):
        query = query.where(QuizAttempt.student_id == current_user.id)

    res = await db.execute(query.order_by(QuizAttempt.submitted_at.desc()))
    attempts = res.scalars().all()

    # lookup student names for teachers
    student_map: Dict[int, User] = {}
    if _is_teacher(current_user):
        student_ids = list({a.student_id for a in attempts})
        if student_ids:
            res = await db.execute(select(User).where(User.id.in_(student_ids)))
            student_map = {u.id: u for u in res.scalars().all()}

    return [
        {
            "id": a.id,
            "student_id": a.student_id,
            "student_name": (student_map.get(a.student_id).full_name if student_map.get(a.student_id) else None),
            "score": a.score,
            "max_score": a.max_score,
            "percentage": round(a.percentage or 0.0, 2),
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
        }
        for a in attempts
    ]


@router.get("/{quiz_id}/export")
async def export_quiz_excel(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not _is_teacher(current_user):
        raise HTTPException(status_code=403, detail="Hanya guru/admin yang dapat mengekspor")

    res = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = res.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Kuis tidak ditemukan")

    res = await db.execute(
        select(QuizAttempt).where(QuizAttempt.quiz_id == quiz_id).order_by(QuizAttempt.submitted_at)
    )
    attempts = res.scalars().all()

    student_ids = list({a.student_id for a in attempts})
    student_map: Dict[int, User] = {}
    if student_ids:
        res = await db.execute(select(User).where(User.id.in_(student_ids)))
        student_map = {u.id: u for u in res.scalars().all()}

    wb = Workbook()
    ws = wb.active
    ws.title = "Hasil Kuis"

    headers = ["No", "Nama Siswa", "Email", "Skor", "Maks", "Persentase", "Waktu Submit"]
    ws.append(headers)

    for idx, a in enumerate(attempts, start=1):
        student = student_map.get(a.student_id)
        ws.append([
            idx,
            student.full_name if student else f"Siswa #{a.student_id}",
            student.email if student else "",
            float(a.score or 0),
            float(a.max_score or 0),
            round(a.percentage or 0.0, 2),
            a.submitted_at.strftime("%Y-%m-%d %H:%M") if a.submitted_at else "",
        ])

    # Soal sheet
    ws2 = wb.create_sheet("Soal & Kunci")
    ws2.append(["No", "Pertanyaan", "Tipe", "Jawaban Benar", "Poin"])
    for idx, q in enumerate(quiz.questions or [], start=1):
        ws2.append([
            idx,
            q.get("question", ""),
            q.get("type", ""),
            q.get("correct_answer", ""),
            q.get("points", 10),
        ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    filename = f"hasil_kuis_{quiz_id}_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
