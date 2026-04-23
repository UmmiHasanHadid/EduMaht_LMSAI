# AI Tutor System Documentation

## Filosofi Pembelajaran

Sistem AI Tutor EduMaht dibangun berdasarkan prinsip:
- **Membimbing, Bukan Menjawab** - AI memberikan petunjuk, bukan jawaban langsung
- **Pembelajaran Positif** - Setiap interaksi dirancang untuk meningkatkan kepercayaan diri siswa
- **Dorong Pemikiran Kritis** - Pertanyaan penuntun mendorong siswa berpikir sendiri

## Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│         Student Answer Input & Tutor Chat Interface          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Routes (/api/ai)                        │
│  - /tutoring/ask (pertanyaan umum)                           │
│  - /tutoring/evaluate (evaluate jawaban)                     │
│  - /tutoring/hint (beri hint)                               │
└─────────────────┬───────────────────────────────────────────┘
                  │
         ┌────────┴────────┐
         ▼                  ▼
    ┌─────────────┐   ┌──────────────────┐
    │ Tutoring    │   │ Answer           │
    │ Service     │   │ Evaluator        │
    └────┬────────┘   └────────┬─────────┘
         │                     │
    ┌────┴──────────┬──────────┘
    ▼               ▼
┌────────────────────────────────┐
│  Gemini AI (ChatGoogleGenerativeAI)
│  ├─ System Prompt (Tutor Config)
│  ├─ User Prompt (Question/Answer)
│  └─ Constraints & Guidelines
└────────────────────────────────┘
```

## Komponen Utama

### 1. **tutor_config.py** - Konfigurasi AI Tutor
Berisi:
- `TUTORING_SYSTEM_PROMPT` - Instruksi ketat untuk Gemini AI
- `ANSWER_EVALUATION_PROMPT` - Template untuk evaluate jawaban
- `SAFE_RESPONSE_TEMPLATES` - Template respon yang sudah disetujui
- `TUTOR_PERSONALITY` - Kepribadian tutor (tone, formality, dll)

**Aturan Ketat yang Diimplementasikan:**
```python
TIDAK BOLEH:
- Memberikan jawaban langsung
- Memberikan formula/rumus lengkap
- Membuat kalimat ambigu
- Membuat siswa merasa bodoh

HARUS:
- Memberikan petunjuk dalam bentuk pertanyaan
- Apresiasi setiap usaha siswa
- Pujian spesifik untuk jawaban benar
- Dorongan konstruktif untuk jawaban salah
```

### 2. **tutoring_service.py** - Layanan Tutoring
Implements:
- `answer_student_question()` - Menjawab pertanyaan siswa dengan membimbing
- `evaluate_and_respond_to_answer()` - Evaluate dan beri feedback
- `provide_hint()` - Memberikan hint tanpa jawaban
- `generate_follow_up_questions()` - Generate pertanyaan lanjutan

### 3. **answer_evaluator.py** - Evaluasi Jawaban
Fungsi:
- `evaluate_answer()` - Evaluasi jawaban siswa vs jawaban benar
- `semantic_similarity()` - Hitung kesamaan semantik
- `determine_feedback_type()` - Tentukan tipe feedback yang tepat

Returns:
```json
{
    "is_correct": boolean,
    "correctness_level": "correct|partial|incorrect",
    "confidence": 0.0-1.0,
    "positive_aspects": "string",
    "conceptual_error": "string",
    "key_points_missed": ["string"],
    "reasoning": "string"
}
```

## Alur Workflow

### 1. Student Asks Question
```
Frontend: POST /api/ai/tutoring/ask
Body: {
    "question": "Bagaimana cara menyelesaikan persamaan kuadrat?",
    "course_id": 1,
    "topic": "Matematika - Persamaan Kuadrat"
}

Response: {
    "response": "Ingat bentuk umum: ax² + bx + c = 0. Coba tanyakan pada diri Anda: apa saja cara yang Anda ketahui untuk menyelesaikannya?",
    "type": "guidance",
    "is_directed": true
}
```

### 2. Student Submits Answer
```
Frontend: POST /api/ai/tutoring/evaluate
Body: {
    "question": "Berapa hasil dari 2x² + 5x + 3 = 0?",
    "student_answer": "x = -1 atau x = -1.5",
    "correct_answer": "x = -1 atau x = -3/2",
    "difficulty_level": "medium"
}

Response: {
    "is_correct": true,
    "correctness_level": "correct",
    "confidence": 0.95,
    "feedback": "Sempurna! Anda memahami cara menyelesaikan persamaan kuadrat dengan sangat baik.",
    "next_step": "celebration",
    "evaluation_details": {...}
}
```

### 3. Student Requests Hint
```
Frontend: POST /api/ai/tutoring/hint
Body: {
    "question": "Berapa hasil dari 2x² + 5x + 3 = 0?",
    "current_attempt": "Saya tidak tahu cara memulai",
    "topic": "Persamaan Kuadrat"
}

Response: {
    "hint": "Coba ingat kembali rumus kuadrat. Apa nilai a, b, dan c dalam persamaan ini? Mulai dari sini!",
    "type": "guiding_question",
    "is_safe": true
}
```

## Response Types

### Ketika Jawaban BENAR ✓

**Respon Template:**
```
"Sempurna! Anda memahami [konsep] dengan sangat baik. 
Penjelasannya menunjukkan pemikiran yang mendalam."
```

**Fitur:**
- Pujian spesifik (bukan hanya "benar")
- Penjelasan MENGAPA jawaban benar
- Encouragement untuk topik lebih lanjut
- Positive reinforcement

### Ketika Jawaban SEBAGIAN BENAR ⚠️

**Respon Template:**
```
"Bagian [spesifik aspek] sudah benar! Sekarang coba perhatikan 
[aspek lain]. Apa yang bisa Anda temukan di sana?"
```

**Fitur:**
- Apresiasi bagian yang benar
- Guide ke bagian yang masih salah
- Pertanyaan penuntun, bukan jawaban
- Mindset: "hampir mendekati"

### Ketika Jawaban SALAH ✗

**Respon Template:**
```
"Terima kasih sudah mencoba! Mari kita telusuri [aspek spesifik] 
dari awal. Apa yang Anda ingat tentang [konsep kunci]?"
```

**Fitur:**
- Apresiasi usaha siswa
- Tidak mengatakan "salah/tidak benar"
- Reframe sebagai "kesempatan belajar"
- Guidance step-by-step
- Positive reframing

## Security & Constraints

### 1. Content Filtering
```python
ALLOWED_TOPICS: mathematics, science, history, literature, 
               languages, technology, arts

BLOCKED_TOPICS: violence, hate, sexual, discrimination
```

### 2. Response Constraints
```python
MAX_RESPONSE_LENGTH: 300 characters
MAX_FOLLOW_UPS: 3 questions per response
TEMPERATURE: 0.3 (untuk evaluasi), 0.7 (untuk guidance)
```

### 3. API Rate Limiting
- Students can ask/evaluate max 10 times per minute (implement in middleware)
- Lazy loading untuk menghindari overload

## Environment Variables

```env
# Required for AI Tutor
GOOGLE_API_KEY=AIzaSyDHMX7NCOKUTVqxZ8txoECTb82CbIvX4ag

# Optional for OpenAI backup
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
```

## Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/ai/tutoring/ask` | Menjawab pertanyaan dengan membimbing |
| POST | `/api/ai/tutoring/evaluate` | Evaluate jawaban & beri feedback |
| POST | `/api/ai/tutoring/hint` | Memberikan hint berbasis jawaban |
| GET | `/api/ai/learning-path/my-path` | Get learning path siswa (coming) |
| POST | `/api/ai/content/generate` | Generate content (coming) |
| GET | `/api/ai/analytics/performance` | Analytics (coming) |

## Best Practices untuk Frontend

### 1. Answer Form Component
```jsx
<AnswerForm onSubmit={async (answer) => {
    const response = await api.post('/api/ai/tutoring/evaluate', {
        question: questionData.question,
        student_answer: answer,
        correct_answer: questionData.answer
    });
    
    // Show feedback berdasarkan correctness_level
    if (response.data.is_correct) {
        showCelebration();
    } else if (response.data.correctness_level === 'partial') {
        showRefinementHint();
    } else {
        showDetailedGuidance();
    }
}} />
```

### 2. Hint Button
```jsx
<HintButton onClick={async () => {
    const hint = await api.post('/api/ai/tutoring/hint', {
        question: questionData.question,
        current_attempt: userAttempt
    });
    showHint(hint.data.hint);
}} />
```

### 3. Never Reveal Correct Answer
```jsx
// JANGAN DO INI - Siswa akan hanya copy jawaban
const showCorrectAnswer = () => { /* BAD */ }

// DO INI - Bimbing siswa untuk temukan sendiri
const showHint = () => { /* GOOD */ }
```

## Monitoring & Logging

Log setiap evaluasi untuk:
- Track student progress
- Identify common misconceptions
- Improve AI prompts
- Adjust difficulty levels

```python
# Log struktur
log_entry = {
    "student_id": 123,
    "timestamp": "2024-04-22T10:30:00Z",
    "question": "...",
    "student_answer": "...",
    "correctness": "correct|partial|incorrect",
    "feedback_given": "...",
    "time_taken_seconds": 45
}
```

## Roadmap

- [ ] Persist student progress & learning analytics
- [ ] Adaptive difficulty based on performance
- [ ] Multi-language support
- [ ] Voice input/output for accessibility
- [ ] Gamification (badges, points)
- [ ] Teacher dashboard untuk monitor students
- [ ] Integration dengan assessment system
