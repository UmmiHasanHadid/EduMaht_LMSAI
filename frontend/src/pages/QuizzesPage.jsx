import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, Button, Card, CardContent, Chip, CircularProgress, Dialog, DialogActions,
  DialogContent, DialogTitle, Divider, FormControl, Grid, IconButton, InputLabel,
  MenuItem, Select, Stack, TextField, Typography, Alert, Tooltip,
} from '@mui/material'
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh'
import AddIcon from '@mui/icons-material/Add'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import TableChartIcon from '@mui/icons-material/TableChart'
import DeleteIcon from '@mui/icons-material/Delete'
import PollIcon from '@mui/icons-material/Poll'

import { quizService } from '../services/quizService'
import { useAuthStore } from '../stores/authStore'

function GenerateDialog({ open, onClose, isTeacher, onCreated }) {
  const [form, setForm] = useState({ topic: '', num_questions: 8, difficulty: 'medium', save_as_quiz: false, title: '' })
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const runGenerate = async () => {
    setError(''); setLoading(true); setPreview(null)
    try {
      const res = await quizService.generate({
        topic: form.topic,
        num_questions: Number(form.num_questions),
        difficulty: form.difficulty,
        save_as_quiz: isTeacher && form.save_as_quiz,
        title: form.title || undefined,
      })
      if (res.saved) {
        onCreated?.()
        onClose()
      } else {
        setPreview(res.preview)
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Gagal membuat kuis')
    } finally { setLoading(false) }
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ fontWeight: 800 }}>Generate Kuis dengan AI</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2}>
          <TextField label="Topik" value={form.topic} onChange={(e) => setForm({ ...form, topic: e.target.value })}
            placeholder="Contoh: Fotosintesis, Persamaan Kuadrat, Sejarah Kemerdekaan"
            inputProps={{ 'data-testid': 'gen-topic-input' }}
          />
          <Stack direction="row" spacing={2}>
            <TextField type="number" label="Jumlah soal" value={form.num_questions}
              onChange={(e) => setForm({ ...form, num_questions: e.target.value })} inputProps={{ min: 3, max: 15, 'data-testid': 'gen-num-input' }} />
            <FormControl fullWidth>
              <InputLabel>Tingkat</InputLabel>
              <Select value={form.difficulty} label="Tingkat" onChange={(e) => setForm({ ...form, difficulty: e.target.value })}
                data-testid="gen-difficulty-select">
                <MenuItem value="easy">Mudah</MenuItem>
                <MenuItem value="medium">Sedang</MenuItem>
                <MenuItem value="hard">Sulit</MenuItem>
              </Select>
            </FormControl>
          </Stack>
          {isTeacher && (
            <>
              <TextField label="Judul (opsional)" value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })} />
              <Stack direction="row" alignItems="center" spacing={1}>
                <input id="save-chk" type="checkbox" checked={form.save_as_quiz}
                  onChange={(e) => setForm({ ...form, save_as_quiz: e.target.checked })}
                  data-testid="gen-save-checkbox"/>
                <label htmlFor="save-chk">
                  <Typography variant="body2">Simpan sebagai kuis (siswa akan bisa mengerjakan)</Typography>
                </label>
              </Stack>
            </>
          )}
          {error && <Alert severity="error">{error}</Alert>}
          {preview && (
            <Alert severity="success">
              Preview {preview.questions?.length || 0} soal berhasil dibuat. {!isTeacher && 'Gunakan sebagai latihan; tidak disimpan.'}
            </Alert>
          )}
          {preview?.questions?.slice(0, 3).map((q, i) => (
            <Card key={i} variant="outlined" sx={{ p: 1.5 }}>
              <Typography sx={{ fontWeight: 700, mb: 0.5 }}>{i + 1}. {q.question}</Typography>
              {q.options?.map((o, j) => <Typography key={j} variant="body2">• {o}</Typography>)}
            </Card>
          ))}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} data-testid="gen-cancel-btn">Tutup</Button>
        <Button onClick={runGenerate} variant="contained" startIcon={loading ? <CircularProgress size={16} /> : <AutoFixHighIcon />} disabled={loading || !form.topic}
          data-testid="gen-submit-btn">
          {isTeacher && form.save_as_quiz ? 'Generate & Simpan' : 'Generate'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

function ManualCreateDialog({ open, onClose, onCreated }) {
  const [form, setForm] = useState({
    title: '', description: '', topic: '', difficulty: 'medium', time_limit_minutes: 30,
    questions: [{ id: 1, type: 'multiple_choice', question: '', options: ['', '', '', ''], correct_answer: '', points: 10 }],
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const updateQ = (idx, patch) => {
    const qs = form.questions.map((q, i) => (i === idx ? { ...q, ...patch } : q))
    setForm({ ...form, questions: qs })
  }
  const addQ = () => setForm({ ...form, questions: [...form.questions, { id: form.questions.length + 1, type: 'multiple_choice', question: '', options: ['', '', '', ''], correct_answer: '', points: 10 }] })
  const removeQ = (idx) => setForm({ ...form, questions: form.questions.filter((_, i) => i !== idx) })

  const submit = async () => {
    setError(''); setLoading(true)
    try {
      await quizService.create(form)
      onCreated?.(); onClose()
    } catch (e) {
      setError(e.response?.data?.detail || 'Gagal membuat kuis')
    } finally { setLoading(false) }
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle sx={{ fontWeight: 800 }}>Buat Kuis Manual (Guru)</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2}>
          <Stack direction="row" spacing={2}>
            <TextField fullWidth label="Judul" value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              inputProps={{ 'data-testid': 'manual-title-input' }}
            />
            <FormControl sx={{ minWidth: 140 }}>
              <InputLabel>Tingkat</InputLabel>
              <Select value={form.difficulty} label="Tingkat"
                onChange={(e) => setForm({ ...form, difficulty: e.target.value })}>
                <MenuItem value="easy">Mudah</MenuItem>
                <MenuItem value="medium">Sedang</MenuItem>
                <MenuItem value="hard">Sulit</MenuItem>
              </Select>
            </FormControl>
          </Stack>
          <TextField multiline minRows={2} label="Deskripsi" value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}/>

          <Divider>Pertanyaan</Divider>

          {form.questions.map((q, idx) => (
            <Card key={idx} variant="outlined" sx={{ p: 2 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                <Typography sx={{ fontWeight: 700 }}>Soal #{idx + 1}</Typography>
                <IconButton size="small" onClick={() => removeQ(idx)}><DeleteIcon fontSize="small" /></IconButton>
              </Stack>
              <Stack direction="row" spacing={2} sx={{ mb: 1 }}>
                <FormControl sx={{ minWidth: 170 }}>
                  <InputLabel>Tipe</InputLabel>
                  <Select value={q.type} label="Tipe" onChange={(e) => updateQ(idx, { type: e.target.value })}>
                    <MenuItem value="multiple_choice">Pilihan Ganda</MenuItem>
                    <MenuItem value="short_answer">Isian Singkat</MenuItem>
                  </Select>
                </FormControl>
                <TextField type="number" label="Poin" value={q.points}
                  onChange={(e) => updateQ(idx, { points: Number(e.target.value) })} sx={{ width: 120 }} />
              </Stack>
              <TextField fullWidth label="Pertanyaan" value={q.question}
                onChange={(e) => updateQ(idx, { question: e.target.value })} sx={{ mb: 1 }}
                inputProps={{ 'data-testid': `manual-question-${idx}` }} />
              {q.type === 'multiple_choice' && (
                <Grid container spacing={1} sx={{ mb: 1 }}>
                  {q.options.map((opt, oi) => (
                    <Grid item xs={12} sm={6} key={oi}>
                      <TextField fullWidth label={`Opsi ${oi + 1}`} value={opt}
                        onChange={(e) => {
                          const options = q.options.slice()
                          options[oi] = e.target.value
                          updateQ(idx, { options })
                        }}/>
                    </Grid>
                  ))}
                </Grid>
              )}
              <TextField fullWidth label="Jawaban benar (persis seperti salah satu opsi untuk MCQ)"
                value={q.correct_answer} onChange={(e) => updateQ(idx, { correct_answer: e.target.value })}
                inputProps={{ 'data-testid': `manual-answer-${idx}` }}/>
            </Card>
          ))}
          <Button startIcon={<AddIcon />} onClick={addQ} data-testid="manual-add-question-btn">Tambah soal</Button>

          {error && <Alert severity="error">{error}</Alert>}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Batal</Button>
        <Button variant="contained" onClick={submit} disabled={loading || !form.title || form.questions.length === 0}
          data-testid="manual-submit-btn">
          {loading ? <CircularProgress size={18} /> : 'Simpan Kuis'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default function QuizzesPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [quizzes, setQuizzes] = useState([])
  const [loading, setLoading] = useState(true)
  const [genOpen, setGenOpen] = useState(false)
  const [manualOpen, setManualOpen] = useState(false)
  const [error, setError] = useState('')

  const isTeacher = user?.role === 'instructor' || user?.role === 'admin'

  const load = async () => {
    setLoading(true)
    try {
      const data = await quizService.list()
      setQuizzes(data || [])
    } catch (e) {
      setError(e.response?.data?.detail || 'Gagal memuat kuis')
    } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const remove = async (id) => {
    if (!confirm('Hapus kuis ini?')) return
    try { await quizService.remove(id); load() } catch (e) { setError(e.response?.data?.detail || 'Gagal hapus') }
  }

  const exportExcel = async (id) => {
    try { await quizService.exportExcel(id) } catch (e) { setError(e.message) }
  }

  return (
    <Box data-testid="quizzes-page">
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems={{ sm: 'center' }} sx={{ mb: 2.5 }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" sx={{ fontWeight: 800 }}>Kuis</Typography>
          <Typography color="text.secondary">
            {isTeacher ? 'Generate soal dengan AI atau buat manual, lalu pantau hasil siswa.' : 'Latihan & kuis dari guru/AI untuk mengukur pemahamanmu.'}
          </Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" startIcon={<AutoFixHighIcon />} onClick={() => setGenOpen(true)}
            data-testid="open-generate-btn">
            Generate AI
          </Button>
          {isTeacher && (
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setManualOpen(true)}
              data-testid="open-manual-btn">
              Buat Kuis
            </Button>
          )}
        </Stack>
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

      {loading ? (
        <Box sx={{ display: 'grid', placeItems: 'center', py: 6 }}><CircularProgress /></Box>
      ) : quizzes.length === 0 ? (
        <Card sx={{ p: 6, textAlign: 'center' }}>
          <PollIcon sx={{ fontSize: 60, color: 'primary.main', opacity: 0.7 }} />
          <Typography variant="h6" sx={{ mt: 1, fontWeight: 700 }}>Belum ada kuis</Typography>
          <Typography color="text.secondary">
            {isTeacher ? 'Coba Generate AI di pojok kanan atas.' : 'Guru belum menerbitkan kuis. Anda tetap bisa latihan sendiri dengan Generate AI.'}
          </Typography>
        </Card>
      ) : (
        <Grid container spacing={2}>
          {quizzes.map((q) => (
            <Grid item xs={12} sm={6} md={4} key={q.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }} data-testid={`quiz-card-${q.id}`}>
                <CardContent sx={{ flex: 1 }}>
                  <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                    <Chip size="small" color={q.source === 'system' ? 'info' : 'secondary'}
                      label={q.source === 'system' ? 'AI-Generated' : 'Guru'} />
                    <Chip size="small" label={q.difficulty} variant="outlined" />
                  </Stack>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>{q.title}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ minHeight: 40 }}>
                    {q.description || q.topic || 'Kuis latihan EduMaht.'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {q.question_count} soal · {q.time_limit_minutes} menit
                  </Typography>
                </CardContent>
                <Box sx={{ p: 1.5, pt: 0 }}>
                  <Stack direction="row" spacing={1}>
                    <Button variant="contained" size="small" startIcon={<PlayArrowIcon />}
                      onClick={() => navigate(`/quizzes/${q.id}/take`)} fullWidth
                      data-testid={`take-quiz-${q.id}-btn`}>
                      Kerjakan
                    </Button>
                    {isTeacher && (
                      <>
                        <Tooltip title="Ekspor hasil Excel">
                          <IconButton color="primary" onClick={() => exportExcel(q.id)}
                            data-testid={`export-quiz-${q.id}-btn`}>
                            <TableChartIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Hapus kuis">
                          <IconButton color="error" onClick={() => remove(q.id)}
                            data-testid={`delete-quiz-${q.id}-btn`}>
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </>
                    )}
                  </Stack>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <GenerateDialog open={genOpen} onClose={() => setGenOpen(false)} isTeacher={isTeacher} onCreated={load} />
      {isTeacher && <ManualCreateDialog open={manualOpen} onClose={() => setManualOpen(false)} onCreated={load} />}
    </Box>
  )
}
