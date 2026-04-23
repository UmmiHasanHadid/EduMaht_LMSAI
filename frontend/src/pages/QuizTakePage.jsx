import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Box, Card, CardContent, Typography, Button, Stack, CircularProgress, Radio,
  RadioGroup, FormControlLabel, TextField, LinearProgress, Chip, Alert, Divider,
} from '@mui/material'
import { quizService } from '../services/quizService'

export default function QuizTakePage() {
  const { quizId } = useParams()
  const navigate = useNavigate()
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    quizService.get(quizId).then(setQuiz).catch((e) => setError(e.response?.data?.detail || 'Gagal memuat kuis'))
  }, [quizId])

  if (error) return <Alert severity="error" data-testid="quiz-load-error">{error}</Alert>
  if (!quiz) return <Box sx={{ display: 'grid', placeItems: 'center', py: 8 }}><CircularProgress /></Box>

  const total = quiz.questions.length
  const answered = Object.keys(answers).filter((k) => (answers[k] || '').length > 0).length
  const progress = total === 0 ? 0 : (answered / total) * 100

  const setAns = (qid, val) => setAnswers((a) => ({ ...a, [String(qid)]: val }))

  const submit = async () => {
    setSubmitting(true); setError('')
    try {
      const res = await quizService.submit(quizId, answers)
      setResult(res)
    } catch (e) {
      setError(e.response?.data?.detail || 'Gagal submit')
    } finally { setSubmitting(false) }
  }

  if (result) {
    return (
      <Box data-testid="quiz-result">
        <Card sx={{ p: 3, mb: 2, background: 'linear-gradient(135deg, #4F46E5 0%, #F59E0B 140%)', color: '#fff' }}>
          <Typography variant="overline" sx={{ opacity: 0.9 }}>Hasil Kuis</Typography>
          <Typography variant="h3" sx={{ fontWeight: 800, mt: 0.5 }}>{result.percentage}%</Typography>
          <Typography>Skor {result.score} dari {result.max_score}</Typography>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5 }}>Pembahasan</Typography>
            <Stack spacing={1.5}>
              {result.details.map((d, i) => (
                <Card key={i} variant="outlined" sx={{ p: 2, borderColor: d.is_correct ? 'success.main' : 'error.main' }}
                  data-testid={`result-item-${i}`}>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
                    <Chip size="small" color={d.is_correct ? 'success' : 'error'}
                      label={d.is_correct ? 'Benar' : 'Salah'}/>
                    <Typography sx={{ fontWeight: 700 }}>{i + 1}. {d.question}</Typography>
                  </Stack>
                  <Typography variant="body2">Jawaban kamu: <b>{d.your_answer || '—'}</b></Typography>
                  <Typography variant="body2">Jawaban benar: <b>{d.correct_answer}</b></Typography>
                  {d.explanation && <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{d.explanation}</Typography>}
                </Card>
              ))}
            </Stack>
            <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
              <Button variant="contained" onClick={() => navigate('/quizzes')} data-testid="result-back-btn">Kembali ke daftar kuis</Button>
              <Button onClick={() => window.location.reload()} data-testid="result-retry-btn">Coba lagi</Button>
            </Stack>
          </CardContent>
        </Card>
      </Box>
    )
  }

  return (
    <Box data-testid="quiz-take-page">
      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" sx={{ fontWeight: 800 }}>{quiz.title}</Typography>
          <Typography color="text.secondary">
            {quiz.description || 'Kerjakan soal di bawah ini dengan teliti.'}
          </Typography>
        </Box>
        <Chip label={quiz.source === 'system' ? 'AI-Generated' : 'Guru'} color={quiz.source === 'system' ? 'info' : 'secondary'} />
      </Stack>

      <Box sx={{ mb: 2 }}>
        <LinearProgress variant="determinate" value={progress} />
        <Typography variant="caption" color="text.secondary">Terjawab {answered}/{total}</Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

      <Stack spacing={2}>
        {quiz.questions.map((q, i) => (
          <Card key={q.id || i} data-testid={`question-${q.id || i}`}>
            <CardContent>
              <Typography sx={{ fontWeight: 700, mb: 1.25 }}>{i + 1}. {q.question}</Typography>
              {q.type === 'multiple_choice' ? (
                <RadioGroup
                  value={answers[String(q.id)] || ''}
                  onChange={(e) => setAns(q.id, e.target.value)}
                >
                  {(q.options || []).map((o, j) => (
                    <FormControlLabel key={j} value={o} control={<Radio />}
                      label={o} data-testid={`answer-${q.id}-opt-${j}`} />
                  ))}
                </RadioGroup>
              ) : (
                <TextField fullWidth multiline minRows={2} placeholder="Tulis jawabanmu…"
                  value={answers[String(q.id)] || ''} onChange={(e) => setAns(q.id, e.target.value)}
                  inputProps={{ 'data-testid': `answer-${q.id}-input` }}
                />
              )}
            </CardContent>
          </Card>
        ))}
      </Stack>

      <Divider sx={{ my: 3 }} />
      <Stack direction="row" justifyContent="flex-end" spacing={1}>
        <Button onClick={() => navigate('/quizzes')}>Batal</Button>
        <Button variant="contained" size="large" onClick={submit} disabled={submitting}
          data-testid="submit-quiz-btn">
          {submitting ? <CircularProgress size={22} /> : 'Kirim Jawaban'}
        </Button>
      </Stack>
    </Box>
  )
}
