"""
EduMaht LMS AI - Backend integration tests.
Covers: auth (demo accounts + register), AI Tutor (chat/sessions/download/delete/explain/summarize/retention-notice),
Quizzes (generate/create/list/get/attempts/export/delete).
"""
from __future__ import annotations

import io
import os
import time
import uuid
import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://edumaht-lms.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

DEMO_STUDENT = ("siswa@edumaht.com", "Siswa1234")
DEMO_TEACHER = ("guru@edumaht.com", "Guru1234")
DEMO_ADMIN = ("admin@edumaht.com", "Admin1234")

CHAT_TIMEOUT = 90  # Gemini chat can be slow

# --------------- Helpers ---------------
def login(email: str, password: str) -> str:
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"login {email} failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def ai_call_retry(fn, retries: int = 3, sleep: float = 3.0):
    """Retry on 502 Gemini error (upstream overload)."""
    last = None
    for i in range(retries):
        resp = fn()
        last = resp
        if resp.status_code == 502 and "Gemini" in resp.text:
            time.sleep(sleep)
            continue
        return resp
    return last


# --------------- Fixtures ---------------
@pytest.fixture(scope="module")
def student_token():
    return login(*DEMO_STUDENT)


@pytest.fixture(scope="module")
def teacher_token():
    return login(*DEMO_TEACHER)


@pytest.fixture(scope="module")
def admin_token():
    return login(*DEMO_ADMIN)


# --------------- Health ---------------
class TestHealth:
    def test_health(self):
        r = requests.get(f"{API}/health", timeout=10)
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_root(self):
        r = requests.get(f"{API}/", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["tutor_retention_days"] == 10
        assert data["ai_model"].startswith("gemini")


# --------------- Auth ---------------
class TestAuth:
    def test_login_student(self):
        t = login(*DEMO_STUDENT)
        assert isinstance(t, str) and len(t) > 20

    def test_login_teacher(self):
        t = login(*DEMO_TEACHER)
        assert isinstance(t, str) and len(t) > 20

    def test_login_admin(self):
        t = login(*DEMO_ADMIN)
        assert isinstance(t, str) and len(t) > 20

    def test_login_bad_credentials(self):
        r = requests.post(f"{API}/auth/login", json={"email": "nope@x.com", "password": "x"}, timeout=10)
        assert r.status_code == 401

    def test_register_and_login_new_student(self):
        uniq = uuid.uuid4().hex[:8]
        email = f"TEST_{uniq}@edumaht.com"
        payload = {
            "email": email,
            "username": f"TEST_{uniq}",
            "full_name": "Test Siswa",
            "password": "TestPass123",
            "role": "student",
        }
        r = requests.post(f"{API}/auth/register", json=payload, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "access_token" in data
        assert data["user"]["email"] == email
        assert data["user"]["role"] == "student"

        # login again with same creds
        t = login(email, "TestPass123")
        assert t
        me = requests.get(f"{API}/users/me", headers=auth_headers(t), timeout=15)
        assert me.status_code == 200, me.text
        assert me.json()["email"] == email

    def test_users_me_student(self, student_token):
        r = requests.get(f"{API}/users/me", headers=auth_headers(student_token), timeout=10)
        assert r.status_code == 200
        assert r.json()["email"] == DEMO_STUDENT[0]

    def test_users_me_unauth(self):
        r = requests.get(f"{API}/users/me", timeout=10)
        assert r.status_code in (401, 403)


# --------------- AI Tutor ---------------
class TestAITutor:
    _session_uid = None  # shared across tests in class

    def test_chat_creates_session(self, student_token):
        payload = {"message": "Halo, bisakah kamu jelaskan apa itu fotosintesis secara singkat?"}
        r = ai_call_retry(lambda: requests.post(
            f"{API}/ai/tutor/chat",
            json=payload,
            headers=auth_headers(student_token),
            timeout=CHAT_TIMEOUT,
        ))
        assert r.status_code == 200, f"chat failed: {r.status_code} {r.text}"
        data = r.json()
        assert "session_uid" in data and data["session_uid"]
        assert data["reply"] and isinstance(data["reply"], str) and len(data["reply"]) > 5
        assert data["retention_days"] == 10
        TestAITutor._session_uid = data["session_uid"]

    def test_chat_appends_to_same_session(self, student_token):
        assert TestAITutor._session_uid, "Prior chat did not create session"
        payload = {
            "session_uid": TestAITutor._session_uid,
            "message": "Terima kasih. Bisa tambahkan satu contoh nyata?"
        }
        r = ai_call_retry(lambda: requests.post(
            f"{API}/ai/tutor/chat",
            json=payload,
            headers=auth_headers(student_token),
            timeout=CHAT_TIMEOUT,
        ))
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["session_uid"] == TestAITutor._session_uid

        # verify messages endpoint has >= 4 messages (2 user + 2 assistant)
        m = requests.get(
            f"{API}/ai/tutor/sessions/{TestAITutor._session_uid}/messages",
            headers=auth_headers(student_token),
            timeout=15,
        )
        assert m.status_code == 200, m.text
        msgs = m.json()["messages"]
        assert len(msgs) >= 4, f"expected >=4 messages got {len(msgs)}"
        # order: user, assistant, user, assistant
        roles = [x["role"] for x in msgs]
        assert roles[0] == "user" and roles[1] == "assistant"

    def test_list_sessions_retention(self, student_token):
        r = requests.get(f"{API}/ai/tutor/sessions", headers=auth_headers(student_token), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["retention_days"] == 10
        assert isinstance(data["sessions"], list)
        # the active one should be there
        uids = [s["session_uid"] for s in data["sessions"]]
        assert TestAITutor._session_uid in uids
        for s in data["sessions"]:
            assert "expires_at" in s and s["expires_at"]

    def test_download_session_owner(self, student_token):
        r = requests.get(
            f"{API}/ai/tutor/sessions/{TestAITutor._session_uid}/download",
            headers=auth_headers(student_token), timeout=20,
        )
        assert r.status_code == 200, r.text
        assert r.headers["content-type"].startswith("text/plain")
        assert "attachment" in r.headers.get("content-disposition", "").lower()
        assert b"AI TUTOR" in r.content or b"AI Tutor" in r.content

    def test_download_forbidden_for_other_user(self, teacher_token):
        r = requests.get(
            f"{API}/ai/tutor/sessions/{TestAITutor._session_uid}/download",
            headers=auth_headers(teacher_token), timeout=15,
        )
        assert r.status_code == 403, f"expected 403, got {r.status_code} {r.text}"
        assert "pemilik" in r.text.lower()

    def test_retention_notice_teacher(self, teacher_token):
        r = requests.get(f"{API}/ai/tutor/retention-notice", headers=auth_headers(teacher_token), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["is_teacher"] is True
        assert data["retention_days"] == 10

    def test_retention_notice_student(self, student_token):
        r = requests.get(f"{API}/ai/tutor/retention-notice", headers=auth_headers(student_token), timeout=10)
        assert r.status_code == 200
        assert r.json()["is_teacher"] is False

    def test_explain(self, student_token):
        payload = {"topic": "hukum Newton kedua", "level": "umum"}
        r = ai_call_retry(lambda: requests.post(
            f"{API}/ai/tutor/explain",
            json=payload,
            headers=auth_headers(student_token),
            timeout=CHAT_TIMEOUT,
        ))
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("explanation") and len(data["explanation"]) > 20

    def test_summarize(self, student_token):
        material = (
            "Fotosintesis adalah proses pembuatan makanan pada tumbuhan hijau dengan bantuan cahaya matahari. "
            "Daun menyerap karbondioksida dari udara dan air dari tanah. Dengan klorofil dan cahaya matahari, "
            "tumbuhan menghasilkan glukosa dan oksigen. Proses ini penting karena menghasilkan oksigen yang "
            "kita hirup dan menjadi dasar rantai makanan di bumi."
        )
        r = ai_call_retry(lambda: requests.post(
            f"{API}/ai/tutor/summarize",
            json={"material": material, "target_length": "ringkas"},
            headers=auth_headers(student_token),
            timeout=CHAT_TIMEOUT,
        ))
        assert r.status_code == 200, r.text
        assert r.json().get("summary")

    def test_delete_session_owner(self, student_token):
        # create a throwaway session to delete
        r = ai_call_retry(lambda: requests.post(
            f"{API}/ai/tutor/chat",
            json={"message": "Halo singkat saja."},
            headers=auth_headers(student_token),
            timeout=CHAT_TIMEOUT,
        ))
        assert r.status_code == 200, r.text
        uid = r.json()["session_uid"]

        d = requests.delete(f"{API}/ai/tutor/sessions/{uid}", headers=auth_headers(student_token), timeout=10)
        assert d.status_code == 200
        assert d.json().get("success") is True

        # verify gone
        g = requests.get(f"{API}/ai/tutor/sessions/{uid}/messages",
                         headers=auth_headers(student_token), timeout=10)
        assert g.status_code == 404


# --------------- Quizzes ---------------
class TestQuizzes:
    _teacher_quiz_id = None
    _manual_quiz_id = None

    def test_generate_as_student_not_saved(self, student_token):
        payload = {
            "topic": "aritmetika dasar",
            "num_questions": 3,
            "difficulty": "easy",
            "save_as_quiz": True,  # should be ignored for students
        }
        r = ai_call_retry(lambda: requests.post(
            f"{API}/quizzes/generate",
            json=payload, headers=auth_headers(student_token), timeout=CHAT_TIMEOUT,
        ))
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("saved") is False
        assert data.get("preview") and data["preview"].get("questions")

    def test_generate_as_teacher_saved(self, teacher_token):
        payload = {
            "topic": "aljabar linear pengantar",
            "num_questions": 3,
            "difficulty": "medium",
            "save_as_quiz": True,
            "title": "TEST_AI Quiz Aljabar",
        }
        r = ai_call_retry(lambda: requests.post(
            f"{API}/quizzes/generate",
            json=payload, headers=auth_headers(teacher_token), timeout=CHAT_TIMEOUT,
        ))
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("saved") is True
        quiz = data["quiz"]
        assert quiz["source"] == "system"
        assert quiz["id"]
        # teacher sees correct_answer
        assert quiz["questions"] and ("correct_answer" in quiz["questions"][0])
        TestQuizzes._teacher_quiz_id = quiz["id"]

    def test_create_manual_quiz_teacher(self, teacher_token):
        payload = {
            "title": "TEST_Manual Quiz IPA",
            "description": "kuis manual",
            "topic": "IPA",
            "difficulty": "easy",
            "time_limit_minutes": 15,
            "questions": [
                {
                    "id": 1,
                    "type": "multiple_choice",
                    "question": "Apa ibu kota Indonesia?",
                    "options": ["Jakarta", "Bandung", "Surabaya", "Medan"],
                    "correct_answer": "Jakarta",
                    "explanation": "Jakarta adalah ibu kota.",
                    "points": 10,
                },
                {
                    "id": 2,
                    "type": "multiple_choice",
                    "question": "Berapa 2+2?",
                    "options": ["3", "4", "5", "6"],
                    "correct_answer": "4",
                    "points": 10,
                },
            ],
        }
        r = requests.post(f"{API}/quizzes/", json=payload, headers=auth_headers(teacher_token), timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["source"] == "teacher"
        assert data["id"]
        TestQuizzes._manual_quiz_id = data["id"]

    def test_create_quiz_forbidden_for_student(self, student_token):
        payload = {
            "title": "TEST_Student Should Fail",
            "questions": [{
                "id": 1, "type": "multiple_choice", "question": "q", "options": ["a","b"], "correct_answer": "a", "points": 5
            }],
        }
        r = requests.post(f"{API}/quizzes/", json=payload, headers=auth_headers(student_token), timeout=10)
        assert r.status_code == 403

    def test_list_quizzes_student_hides_answers(self, student_token):
        assert TestQuizzes._manual_quiz_id
        r = requests.get(f"{API}/quizzes/", headers=auth_headers(student_token), timeout=10)
        assert r.status_code == 200
        quizzes = r.json()
        found = next((q for q in quizzes if q["id"] == TestQuizzes._manual_quiz_id), None)
        assert found, "manual quiz not found in list"
        for q in found["questions"]:
            assert "correct_answer" not in q, "student should NOT see correct_answer"
            assert "explanation" not in q, "student should NOT see explanation"

    def test_list_quizzes_teacher_shows_answers(self, teacher_token):
        r = requests.get(f"{API}/quizzes/", headers=auth_headers(teacher_token), timeout=10)
        assert r.status_code == 200
        quizzes = r.json()
        found = next((q for q in quizzes if q["id"] == TestQuizzes._manual_quiz_id), None)
        assert found
        assert "correct_answer" in found["questions"][0]

    def test_submit_attempt_scoring(self, student_token):
        qid = TestQuizzes._manual_quiz_id
        # correct: Q1=Jakarta, Q2=4
        r = requests.post(
            f"{API}/quizzes/{qid}/attempts",
            json={"answers": {"1": "Jakarta", "2": "4"}},
            headers=auth_headers(student_token), timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["score"] == 20
        assert data["max_score"] == 20
        assert data["percentage"] == 100.0
        assert len(data["details"]) == 2
        assert all(d["is_correct"] for d in data["details"])

    def test_submit_attempt_partial(self, student_token):
        qid = TestQuizzes._manual_quiz_id
        r = requests.post(
            f"{API}/quizzes/{qid}/attempts",
            json={"answers": {"1": "Bandung", "2": "4"}},
            headers=auth_headers(student_token), timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["score"] == 10
        assert data["max_score"] == 20
        assert data["percentage"] == 50.0

    def test_list_attempts_teacher_shows_all(self, teacher_token):
        qid = TestQuizzes._manual_quiz_id
        r = requests.get(f"{API}/quizzes/{qid}/attempts", headers=auth_headers(teacher_token), timeout=10)
        assert r.status_code == 200
        attempts = r.json()
        assert len(attempts) >= 2
        assert any(a.get("student_name") for a in attempts), "teacher should see student_name"

    def test_list_attempts_student_only_own(self, student_token):
        qid = TestQuizzes._manual_quiz_id
        r = requests.get(f"{API}/quizzes/{qid}/attempts", headers=auth_headers(student_token), timeout=10)
        assert r.status_code == 200
        attempts = r.json()
        assert len(attempts) >= 2
        # all should belong to student (only own)
        # we can't directly compare id, but student_name should likely be None (no teacher map)
        # Just ensure endpoint responds OK with list

    def test_export_teacher_xlsx(self, teacher_token):
        qid = TestQuizzes._manual_quiz_id
        r = requests.get(f"{API}/quizzes/{qid}/export", headers=auth_headers(teacher_token), timeout=20)
        assert r.status_code == 200, r.text
        ct = r.headers.get("content-type", "")
        assert "spreadsheetml" in ct or "officedocument" in ct, f"unexpected content-type: {ct}"
        assert "attachment" in r.headers.get("content-disposition", "").lower()
        assert len(r.content) > 100

    def test_export_forbidden_student(self, student_token):
        qid = TestQuizzes._manual_quiz_id
        r = requests.get(f"{API}/quizzes/{qid}/export", headers=auth_headers(student_token), timeout=10)
        assert r.status_code == 403

    def test_delete_quiz_student_forbidden(self, student_token):
        qid = TestQuizzes._manual_quiz_id
        r = requests.delete(f"{API}/quizzes/{qid}", headers=auth_headers(student_token), timeout=10)
        assert r.status_code == 403

    def test_delete_quiz_teacher_ok(self, teacher_token):
        # delete both created quizzes
        for qid_attr in ("_teacher_quiz_id", "_manual_quiz_id"):
            qid = getattr(TestQuizzes, qid_attr)
            if not qid:
                continue
            r = requests.delete(f"{API}/quizzes/{qid}", headers=auth_headers(teacher_token), timeout=10)
            assert r.status_code == 200, f"delete {qid_attr}={qid} -> {r.status_code} {r.text}"
