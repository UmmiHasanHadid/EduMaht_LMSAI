"""AI Tutor Routes – chat, explain, summarize, quiz-gen, retention"""
from __future__ import annotations

import io
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Course, Lesson, TutorMessage, TutorSession, User, UserRole
from app.utils.auth import get_current_user
from app.ai_services.gemini_tutor import (
    ai_chat_reply,
    ai_explain,
    ai_summarize,
)

router = APIRouter(prefix="/api/ai/tutor", tags=["ai-tutor"])


# ---------------- helpers ----------------
async def _cleanup_expired(db: AsyncSession) -> None:
    """Delete sessions older than tutor_retention_days (default 10)."""
    cutoff = datetime.utcnow() - timedelta(days=settings.tutor_retention_days)
    await db.execute(delete(TutorSession).where(TutorSession.created_at < cutoff))
    await db.commit()


async def _load_course_context(
    db: AsyncSession, course_id: Optional[int], lesson_id: Optional[int]
):
    course_title = lesson_title = material = None
    if course_id:
        res = await db.execute(select(Course).where(Course.id == course_id))
        c = res.scalar_one_or_none()
        if c:
            course_title = c.title
            material = c.description or ""
    if lesson_id:
        res = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
        l = res.scalar_one_or_none()
        if l:
            lesson_title = l.title
            material = (l.content or l.description or material) or ""
    return course_title, lesson_title, material


# ---------------- Request schemas ----------------
class ChatRequest(BaseModel):
    session_uid: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=4000)
    course_id: Optional[int] = None
    lesson_id: Optional[int] = None


class ExplainRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=300)
    course_id: Optional[int] = None
    lesson_id: Optional[int] = None
    level: str = "umum"


class SummarizeRequest(BaseModel):
    material: str = Field(..., min_length=20, max_length=20000)
    target_length: str = "ringkas"


# ---------------- Endpoints ----------------
@router.post("/chat")
async def chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a user message; create session if needed; persist both sides."""
    await _cleanup_expired(db)

    # resolve session (owned by current_user)
    session: Optional[TutorSession] = None
    if data.session_uid:
        res = await db.execute(
            select(TutorSession).where(
                TutorSession.session_uid == data.session_uid,
                TutorSession.user_id == current_user.id,
            )
        )
        session = res.scalar_one_or_none()

    if session is None:
        session = TutorSession(
            session_uid=uuid.uuid4().hex,
            user_id=current_user.id,
            course_id=data.course_id,
            lesson_id=data.lesson_id,
            title=(data.message[:60] + ("..." if len(data.message) > 60 else "")),
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

    # Load existing history (excluding the upcoming user message)
    res = await db.execute(
        select(TutorMessage).where(TutorMessage.session_id == session.id).order_by(TutorMessage.id)
    )
    history = [{"role": m.role, "content": m.content} for m in res.scalars().all()]

    # persist user message
    user_msg = TutorMessage(session_id=session.id, role="user", content=data.message)
    db.add(user_msg)
    await db.commit()

    # context
    course_title, lesson_title, material = await _load_course_context(
        db, data.course_id or session.course_id, data.lesson_id or session.lesson_id
    )

    role_hint = "guru" if current_user.role == UserRole.INSTRUCTOR else ("admin" if current_user.role == UserRole.ADMIN else "siswa")

    try:
        reply_text = await ai_chat_reply(
            session_uid=session.session_uid,
            history=history,
            user_text=data.message,
            course_title=course_title,
            lesson_title=lesson_title,
            material=material,
            role_hint=role_hint,
        )
    except Exception as e:
        msg = str(e).lower()
        is_quota = any(k in msg for k in ["429", "quota", "resource_exhausted", "rate limit"])
        status_code = 429 if is_quota else 502
        detail = (
            "Kuota harian Gemini untuk API key ini habis. Silakan coba lagi besok "
            "atau upgrade paket Gemini."
            if is_quota else f"AI Tutor sedang sibuk: {e}"
        )
        raise HTTPException(status_code=status_code, detail=detail)

    # persist assistant
    asst = TutorMessage(session_id=session.id, role="assistant", content=reply_text)
    db.add(asst)
    session.updated_at = datetime.utcnow()
    await db.commit()

    return {
        "session_uid": session.session_uid,
        "reply": reply_text,
        "created_at": asst.created_at.isoformat() if asst.created_at else datetime.utcnow().isoformat(),
        "retention_days": settings.tutor_retention_days,
    }


@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _cleanup_expired(db)
    res = await db.execute(
        select(TutorSession).where(TutorSession.user_id == current_user.id).order_by(TutorSession.updated_at.desc())
    )
    sessions = res.scalars().all()
    return {
        "retention_days": settings.tutor_retention_days,
        "sessions": [
            {
                "session_uid": s.session_uid,
                "title": s.title,
                "course_id": s.course_id,
                "lesson_id": s.lesson_id,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
                "expires_at": (
                    s.created_at + timedelta(days=settings.tutor_retention_days)
                ).isoformat(),
            }
            for s in sessions
        ],
    }


@router.get("/sessions/{session_uid}/messages")
async def get_session_messages(
    session_uid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(TutorSession).where(
            TutorSession.session_uid == session_uid,
            TutorSession.user_id == current_user.id,
        )
    )
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan")

    res = await db.execute(
        select(TutorMessage).where(TutorMessage.session_id == session.id).order_by(TutorMessage.id)
    )
    messages = [
        {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in res.scalars().all()
    ]
    return {
        "session": {
            "session_uid": session.session_uid,
            "title": session.title,
            "course_id": session.course_id,
            "lesson_id": session.lesson_id,
        },
        "messages": messages,
        "retention_days": settings.tutor_retention_days,
    }


@router.get("/sessions/{session_uid}/download")
async def download_session_txt(
    session_uid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Only the session owner may download. Teachers cannot access students' sessions."""
    res = await db.execute(
        select(TutorSession).where(
            TutorSession.session_uid == session_uid,
            TutorSession.user_id == current_user.id,
        )
    )
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=403,
            detail="Hanya pemilik sesi yang dapat mengunduh percakapan ini.",
        )

    res = await db.execute(
        select(TutorMessage).where(TutorMessage.session_id == session.id).order_by(TutorMessage.id)
    )
    lines = [
        f"# Percakapan AI Tutor EduMaht",
        f"Sesi: {session.title}",
        f"Dibuat: {session.created_at.isoformat()}",
        f"Retensi: {settings.tutor_retention_days} hari (otomatis terhapus)",
        "-" * 60,
        "",
    ]
    for m in res.scalars().all():
        who = "SISWA" if m.role == "user" else "AI TUTOR"
        lines.append(f"[{m.created_at.isoformat()}] {who}:")
        lines.append(m.content)
        lines.append("")

    buf = io.BytesIO("\n".join(lines).encode("utf-8"))
    filename = f"tutor_{session.session_uid[:8]}.txt"
    return StreamingResponse(
        buf,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/sessions/{session_uid}")
async def delete_session(
    session_uid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(TutorSession).where(
            TutorSession.session_uid == session_uid,
            TutorSession.user_id == current_user.id,
        )
    )
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan")
    await db.delete(session)
    await db.commit()
    return {"success": True}


@router.post("/explain")
async def explain(
    data: ExplainRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    course_title, lesson_title, material = await _load_course_context(
        db, data.course_id, data.lesson_id
    )
    try:
        text = await ai_explain(
            topic=data.topic,
            course_title=course_title,
            lesson_title=lesson_title,
            material=material,
            level=data.level,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini error: {e}")
    return {"explanation": text}


@router.post("/summarize")
async def summarize(
    data: SummarizeRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        text = await ai_summarize(data.material, target_length=data.target_length)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini error: {e}")
    return {"summary": text}


@router.get("/retention-notice")
async def retention_notice(current_user: User = Depends(get_current_user)):
    """Returned to teachers to remind them about student chat privacy/retention."""
    return {
        "retention_days": settings.tutor_retention_days,
        "message": (
            f"Pengingat: percakapan siswa dengan AI Tutor hanya disimpan selama "
            f"{settings.tutor_retention_days} hari dan BERSIFAT PRIBADI. "
            "Guru tidak dapat melihat atau mengunduh percakapan siswa."
        ),
        "is_teacher": current_user.role in (UserRole.INSTRUCTOR, UserRole.ADMIN),
    }
