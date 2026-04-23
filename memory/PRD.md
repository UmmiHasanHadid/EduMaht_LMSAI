# EduMaht LMS AI - Product Requirements Document

## Original Problem Statement
User uploaded the EduMaht LMS AI source code (ZIP) and asked to continue development of the AI Tutor feature using the Gemini API.

## User Choices (Confirmed)
- **Gemini model**: `gemini-2.5-flash` (primary) with automatic fallback to `gemini-3-flash-preview` and `gemini-2.5-pro` on 503/429.
- **API key**: User-supplied Gemini key (`GEMINI_API_KEY` in backend/.env), not the Emergent Universal Key — so no platform credits are consumed.
- **Features requested**:
  1. Multi-turn Q&A chat with AI Tutor (persistent per user).
  2. Context-aware explanations tied to course/lesson material (both students & teachers).
  3. Summary & feedback capability; ability to download the student's own chat as a `.txt` (teachers CANNOT access student chats).
  4. Quiz generator — two kinds:
     - System-generated (AI) for student self-practice / struggle detection.
     - Teacher-uploaded, with Excel export of student results.
  5. Chat persistence with **auto-delete after 10 days**.
  6. Teachers must see a privacy reminder: "Percakapan siswa tersimpan 10 hari & tidak dapat dilihat/diunduh oleh guru."

## Architecture & Tech Stack
- **Backend**: FastAPI + SQLAlchemy async (SQLite via `aiosqlite`), uvicorn @ 0.0.0.0:8001.
- **AI**: `emergentintegrations` LlmChat → Gemini with user's API key; retry + multi-model fallback.
- **Frontend**: Vite + React 18 + MUI + Zustand + React Router; port 3000; reads `REACT_APP_BACKEND_URL`.
- **DB models**: User, Course, Lesson, Enrollment, Assessment, AssessmentQuestion, LearningPath, Attendance, Grade, **TutorSession, TutorMessage, Quiz, QuizAttempt** (new).

## Core Requirements (Static)
- Roles: `student`, `instructor`, `admin`.
- JWT auth with access+refresh tokens (bcrypt password hashing).
- Role-gated endpoints (quiz create/delete/export = teacher/admin only).
- Student chat privacy (owner-only access to sessions/messages/download/delete).
- 10-day retention enforced via `_cleanup_expired` on every list/chat call (idempotent cutoff by UTC).

## What's Been Implemented (2026-04-23)
### Backend
- Migrated user's ZIP into `/app/backend` with a working entry point (`server.py`).
- Replaced Postgres config with SQLite (zero-config); fixed async/sync engine split.
- Fixed Pydantic v2 validators and async session handling in `AuthService`.
- Seed demo users on startup (guru/siswa/admin).
- **AI Tutor** (`/api/ai/tutor`): `chat`, `sessions`, `messages`, `download` (.txt), `delete`, `explain`, `summarize`, `retention-notice`.
- **Quizzes** (`/api/quizzes`): `generate` (AI), `create` (manual), `list`, `get`, `attempts` (submit/list), `export` (Excel), `delete`.
- Gemini service (`app/ai_services/gemini_tutor.py`): retry + fallback for both 503 and 429 (quota) errors; JSON extraction for quiz.

### Frontend (complete rebuild with modern MUI theme — indigo/amber gradient, Plus Jakarta Sans)
- Login, Register with Indonesian copy & demo-account chips.
- App shell (`Layout`) with glass header, dark-mode toggle, role chip, user menu.
- **Dashboard**: gradient hero, stat cards, recent sessions, quizzes, privacy reminder banner for teachers.
- **AI Tutor page**: chat sidebar, markdown rendering, retention banner, .txt download, delete, teacher privacy modal.
- **Quizzes**: list, AI generate dialog (student gets transient preview, teacher can save), manual create dialog, Excel export (teacher), delete (teacher).
- **QuizTakePage** & **QuizResultsPage**: MCQ/short answer UI, instant scoring, pembahasan per soal.

## Testing Status
- `testing_agent_v3` iteration 1: **31/33 (94%) backend tests passing**.
- 2 failures were Gemini free-tier daily quota (429 RESOURCE_EXHAUSTED) — not a code bug.
- Applied follow-up fix: retry/fallback now also catches 429, and quota errors surface as HTTP 429 with user-friendly message.
- Frontend smoke-tested via Playwright screenshots (login → dashboard → tutor → quizzes all render).

## Known Limits / Operational Notes
- Gemini free-tier: ~20 req/day per model. Heavy testing may temporarily exhaust quota until fallback models have their separate quotas.
- `SECRET_KEY` in `backend/.env` must be rotated before production deploy.
- CORS currently `*`; tighten for prod.

## Roadmap (next tasks)
### P0 (blocking for prod-like demo)
- [ ] Enrollments CRUD UI (backend exists).
- [ ] Course detail page (materials + inline AI Tutor).
- [ ] Per-lesson content upload (teacher) to power context-aware tutoring.
### P1
- [ ] Student struggle-detection: aggregate wrong answers to suggest topics for AI re-teach.
- [ ] Guru dashboard (kelas → siswa → rata-rata nilai) with charts (recharts).
- [ ] Notifications (toast) on quiz submit / chat errors.
### P2
- [ ] Voice input for AI Tutor.
- [ ] Google OAuth login.
- [ ] Mobile layout polish.
- [ ] I18n (currently id-ID only).

## Demo Credentials (in `/app/memory/test_credentials.md`)
- `siswa@edumaht.com` / `Siswa1234`
- `guru@edumaht.com` / `Guru1234`
- `admin@edumaht.com` / `Admin1234`
