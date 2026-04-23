"""
AI Tutor Service using Gemini via emergentintegrations
- Multi-turn chat persisted in DB (per session_uid)
- Context-aware (course/lesson material injected into system prompt)
- Summary & quiz generation with structured JSON output
"""
from __future__ import annotations

import asyncio
import json
import re
import uuid
from typing import Dict, List, Optional

from emergentintegrations.llm.chat import LlmChat, UserMessage

from app.config import settings


TUTOR_SYSTEM_PROMPT = """Kamu adalah **Bu Maht**, AI Tutor EduMaht yang ramah, sabar, dan cerdas.

GAYA MENGAJAR:
- Gunakan Bahasa Indonesia yang hangat, jelas, dan mudah dipahami.
- Berikan penjelasan bertahap (step-by-step), disertai contoh nyata.
- Dorong siswa berpikir dengan pertanyaan penuntun bila mereka bingung.
- Apresiasi setiap usaha; jangan pernah membuat siswa merasa bodoh.
- Gunakan analogi yang relevan untuk konsep sulit.
- Jawaban ringkas-padat-informatif (hindari bertele-tele; max 6 paragraf).
- Dukung rumus/kode dengan format Markdown yang rapi (```) bila perlu.

ATURAN PENTING:
1. Selalu berpegang pada materi kursus/pelajaran yang diberikan dalam KONTEKS.
2. Jika ditanya di luar topik edukasi, arahkan kembali dengan sopan.
3. Jangan pernah berpura-pura tahu hal yang tidak kamu tahu — akui keterbatasan.
4. Saat memberikan jawaban kuis, jelaskan alasannya agar siswa benar-benar paham.
5. Jika guru bertanya, beri jawaban profesional & kaya detail pedagogis.
"""


EXPLAIN_SYSTEM_PROMPT = """Kamu adalah AI penjelas materi EduMaht.
Tugasmu: menjelaskan materi pelajaran dengan SANGAT JELAS, terstruktur, dan memotivasi.
Output selalu dalam Bahasa Indonesia dengan format Markdown:
- Ringkasan 1-2 kalimat
- Poin-poin kunci (bullet)
- Contoh konkret minimal 1
- 2-3 pertanyaan reflektif di akhir untuk memperdalam pemahaman.
"""


QUIZ_SYSTEM_PROMPT = """Kamu adalah generator soal EduMaht.
Tugas: buat soal latihan berkualitas berdasarkan materi/topik yang diminta.
Balas HANYA dengan JSON valid (tanpa penjelasan tambahan & tanpa blok kode Markdown) dengan skema:

{
  "title": "string",
  "description": "string",
  "questions": [
    {
      "id": 1,
      "type": "multiple_choice" | "short_answer",
      "question": "string",
      "options": ["A", "B", "C", "D"],   // hanya untuk multiple_choice
      "correct_answer": "string",         // untuk MCQ isi salah satu option persis
      "explanation": "string",
      "points": 10
    }
  ]
}

Aturan:
- Minimal 5 soal, maksimal 15. Variasikan tingkat kesulitan.
- Untuk MCQ: 4 opsi, hanya 1 benar, distraktor masuk akal.
- Bahasa Indonesia, jelas & tidak ambigu.
"""


def _build_context_block(
    course_title: Optional[str],
    lesson_title: Optional[str],
    material: Optional[str],
) -> str:
    parts: List[str] = []
    if course_title:
        parts.append(f"Kursus: {course_title}")
    if lesson_title:
        parts.append(f"Pelajaran: {lesson_title}")
    if material:
        # keep material reasonably bounded
        snippet = material.strip()
        if len(snippet) > 4000:
            snippet = snippet[:4000] + "..."
        parts.append(f"Materi referensi:\n{snippet}")
    if not parts:
        return ""
    return "\n\nKONTEKS:\n" + "\n".join(parts)


def _make_chat(session_uid: str, system_message: str) -> LlmChat:
    api_key = settings.gemini_api_key or settings.google_api_key
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY belum dikonfigurasi. Tambahkan ke backend/.env."
        )
    chat = LlmChat(
        api_key=api_key,
        session_id=session_uid,
        system_message=system_message,
    ).with_model("gemini", settings.gemini_model)
    return chat


async def _send_with_retry(chat: LlmChat, message: UserMessage, retries: int = 3) -> str:
    """Send a message with small retry to absorb transient 503s from Gemini."""
    last_err: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            reply = await chat.send_message(message)
            return str(reply)
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            # Treat 429 (quota) as non-retriable on THIS model — fallback handler will switch models.
            is_quota = any(k in msg for k in ["429", "rate limit", "ratelimit", "quota", "resource_exhausted"])
            transient = any(k in msg for k in ["503", "unavailable", "overload", "high demand", "timeout"])
            if is_quota:
                raise
            if transient and attempt < retries:
                await asyncio.sleep(1.2 * (attempt + 1))
                continue
            raise
    raise last_err  # pragma: no cover


def _is_fallbackable_error(err: Exception) -> bool:
    """Errors where trying a different model may succeed."""
    msg = str(err).lower()
    return any(
        k in msg
        for k in [
            "503", "unavailable", "overload", "high demand", "timeout",
            "429", "rate limit", "ratelimit", "quota", "resource_exhausted",
        ]
    )


async def _send_with_fallback(session_uid: str, system: str, user_text: str) -> str:
    """Try primary model, fall back to preview/pro on transient OR quota errors."""
    models = [settings.gemini_model, "gemini-3-flash-preview", "gemini-2.5-pro"]
    seen = set()
    ordered = []
    for m in models:
        if m and m not in seen:
            seen.add(m)
            ordered.append(m)

    last_err: Optional[Exception] = None
    for model in ordered:
        chat = LlmChat(
            api_key=(settings.gemini_api_key or settings.google_api_key),
            session_id=session_uid,
            system_message=system,
        ).with_model("gemini", model)
        try:
            return await _send_with_retry(chat, UserMessage(text=user_text), retries=2)
        except Exception as e:
            last_err = e
            if _is_fallbackable_error(e):
                # try next model
                continue
            # non-fallbackable error — abort
            raise
    raise last_err if last_err else RuntimeError("Gemini unavailable")


async def ai_chat_reply(
    session_uid: str,
    history: List[Dict[str, str]],
    user_text: str,
    course_title: Optional[str] = None,
    lesson_title: Optional[str] = None,
    material: Optional[str] = None,
    role_hint: str = "siswa",
) -> str:
    """Send a new user message with past history replayed into the chat."""
    context_block = _build_context_block(course_title, lesson_title, material)
    system = TUTOR_SYSTEM_PROMPT + (
        f"\n\nRole pengguna saat ini: {role_hint}."
    ) + context_block

    # Instead of replaying history (which would make N API calls),
    # compress it into a single "conversation so far" block to save tokens & latency.
    if history:
        last = history[-12:]
        rendered = []
        for m in last:
            who = "Siswa" if m["role"] == "user" else "AI Tutor"
            rendered.append(f"{who}: {m['content']}")
        history_block = "Percakapan sebelumnya:\n" + "\n".join(rendered) + "\n\nPertanyaan saat ini:\n"
        final_user = history_block + user_text
    else:
        final_user = user_text

    reply = await _send_with_fallback(session_uid, system, final_user)
    return reply.strip()


async def ai_explain(
    topic: str,
    course_title: Optional[str] = None,
    lesson_title: Optional[str] = None,
    material: Optional[str] = None,
    level: str = "umum",
) -> str:
    context_block = _build_context_block(course_title, lesson_title, material)
    system = EXPLAIN_SYSTEM_PROMPT + context_block

    prompt = (
        f"Tolong jelaskan topik berikut untuk tingkat '{level}': {topic}.\n"
        "Pastikan penjelasan lengkap, terstruktur, dan memotivasi."
    )
    reply = await _send_with_fallback(f"explain-{uuid.uuid4()}", system, prompt)
    return reply.strip()


async def ai_summarize(material: str, target_length: str = "ringkas") -> str:
    system = EXPLAIN_SYSTEM_PROMPT + "\nGaya ringkasan: " + target_length
    prompt = f"Ringkas materi berikut:\n\n{material}"
    reply = await _send_with_fallback(f"summary-{uuid.uuid4()}", system, prompt)
    return reply.strip()


def _extract_json(text: str) -> dict:
    """Best-effort extract a JSON object from LLM output."""
    text = text.strip()
    # remove fences ```json ... ```
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    # try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # fallback: first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError("Gagal memparse JSON dari respons AI.")


async def ai_generate_quiz(
    topic: str,
    num_questions: int = 8,
    difficulty: str = "medium",
    material: Optional[str] = None,
    question_types: Optional[List[str]] = None,
) -> dict:
    types = question_types or ["multiple_choice", "short_answer"]
    context_block = f"\nMateri referensi:\n{material[:4000]}" if material else ""
    system = QUIZ_SYSTEM_PROMPT + context_block

    prompt = (
        f"Buat {num_questions} soal dengan tingkat kesulitan '{difficulty}' "
        f"tentang topik: {topic}.\n"
        f"Gunakan tipe soal dari: {', '.join(types)}.\n"
        "Balas HANYA JSON sesuai skema."
    )
    raw = await _send_with_fallback(f"quiz-{uuid.uuid4()}", system, prompt)
    data = _extract_json(raw)
    # basic normalization
    for idx, q in enumerate(data.get("questions", []), start=1):
        q.setdefault("id", idx)
        q.setdefault("points", 10)
        if q.get("type") == "multiple_choice" and "options" not in q:
            q["options"] = []
    return data


async def ai_feedback_on_answer(
    question: str,
    correct_answer: str,
    student_answer: str,
) -> str:
    system = (
        "Kamu adalah guru yang memberi feedback konstruktif dalam Bahasa Indonesia. "
        "Awali dengan apresiasi usaha, jelaskan bagian yang benar dan yang perlu diperbaiki, "
        "lalu berikan dorongan positif. Maksimal 4 kalimat."
    )
    prompt = (
        f"Pertanyaan: {question}\n"
        f"Jawaban siswa: {student_answer}\n"
        f"Jawaban ideal: {correct_answer}\n\n"
        "Berikan feedback singkat yang memotivasi."
    )
    reply = await _send_with_fallback(f"fb-{uuid.uuid4()}", system, prompt)
    return reply.strip()
