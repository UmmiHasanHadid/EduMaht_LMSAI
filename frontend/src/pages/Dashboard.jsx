import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, Grid, Card, CardContent, Typography, Button, Stack, Chip, Avatar, LinearProgress,
} from '@mui/material'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import QuizIcon from '@mui/icons-material/Quiz'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import { useAuthStore } from '../stores/authStore'
import { tutorService } from '../services/tutorService'
import { quizService } from '../services/quizService'

export default function Dashboard() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [sessions, setSessions] = useState([])
  const [quizzes, setQuizzes] = useState([])
  const [retention, setRetention] = useState(10)
  const [noticeMessage, setNoticeMessage] = useState('')

  useEffect(() => {
    (async () => {
      try {
        const s = await tutorService.listSessions()
        setSessions(s.sessions || [])
        setRetention(s.retention_days || 10)
      } catch { /* ignore */ }
      try {
        const q = await quizService.list()
        setQuizzes(q || [])
      } catch { /* ignore */ }
      try {
        const n = await tutorService.retentionNotice()
        if (n.is_teacher) setNoticeMessage(n.message)
      } catch { /* ignore */ }
    })()
  }, [])

  const isTeacher = user?.role === 'instructor' || user?.role === 'admin'

  return (
    <Box data-testid="dashboard-page">
      {/* Hero */}
      <Card sx={{
        p: { xs: 3, md: 4 }, mb: 3,
        color: '#fff',
        background: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #F59E0B 120%)',
        position: 'relative', overflow: 'hidden',
      }}>
        <Box sx={{ position: 'absolute', right: -40, top: -40, opacity: 0.2, fontSize: 220 }}>
          <AutoAwesomeIcon sx={{ fontSize: 'inherit' }} />
        </Box>
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
          <Chip size="small" label="Beta" sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: '#fff', fontWeight: 700 }} />
          <Chip size="small" label="AI Tutor: gemini-2.5-flash" sx={{ bgcolor: 'rgba(255,255,255,0.12)', color: '#fff', fontWeight: 600 }} />
        </Stack>
        <Typography variant="h3" sx={{ fontWeight: 800, lineHeight: 1.15 }} data-testid="dashboard-greeting">
          Halo, {user?.full_name?.split(' ')[0] || 'Kawan'} 👋
        </Typography>
        <Typography sx={{ opacity: 0.9, mt: 1, maxWidth: 680 }}>
          Selamat datang di EduMaht — LMS bertenaga AI. {isTeacher
            ? 'Kelola kuis, lihat perkembangan siswa, dan gunakan AI untuk membuat soal dalam hitungan detik.'
            : 'Ngobrol dengan Bu Maht (AI Tutor) untuk bantuan materi, atau latihan soal adaptif yang disesuaikan dengan dirimu.'}
        </Typography>
        <Stack direction="row" spacing={1.5} sx={{ mt: 3 }}>
          <Button
            variant="contained" color="secondary" size="large"
            startIcon={<SmartToyIcon />}
            onClick={() => navigate('/tutor')}
            data-testid="dashboard-open-tutor-btn"
            sx={{ color: '#1F2937' }}
          >
            Mulai Belajar dengan AI
          </Button>
          <Button
            variant="outlined" size="large"
            startIcon={<QuizIcon />}
            onClick={() => navigate('/quizzes')}
            data-testid="dashboard-open-quizzes-btn"
            sx={{ color: '#fff', borderColor: 'rgba(255,255,255,0.7)', '&:hover': { borderColor: '#fff', bgcolor: 'rgba(255,255,255,0.08)' } }}
          >
            {isTeacher ? 'Kelola Kuis' : 'Kerjakan Kuis'}
          </Button>
        </Stack>
      </Card>

      {/* Teacher privacy notice */}
      {isTeacher && noticeMessage && (
        <Card sx={{ mb: 3, p: 2.5, borderLeft: '4px solid', borderColor: 'warning.main', bgcolor: 'warning.light', color: 'warning.dark' }} data-testid="teacher-retention-notice">
          <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 0.5 }}>Pengingat Privasi</Typography>
          <Typography variant="body2">{noticeMessage}</Typography>
        </Card>
      )}

      {/* Stat cards */}
      <Grid container spacing={2.5} sx={{ mb: 3 }}>
        {[
          { label: 'Sesi AI Tutor', value: sessions.length, icon: <SmartToyIcon />, color: 'primary.main' },
          { label: 'Kuis tersedia', value: quizzes.length, icon: <QuizIcon />, color: 'secondary.main' },
          { label: 'Retensi chat (hari)', value: retention, icon: <TrendingUpIcon />, color: 'success.main' },
        ].map((s) => (
          <Grid item xs={12} sm={4} key={s.label}>
            <Card sx={{ p: 2.5 }}>
              <Stack direction="row" spacing={2} alignItems="center">
                <Avatar sx={{ bgcolor: s.color, width: 48, height: 48 }}>{s.icon}</Avatar>
                <Box>
                  <Typography variant="caption" color="text.secondary">{s.label}</Typography>
                  <Typography variant="h4" sx={{ fontWeight: 800 }}>{s.value}</Typography>
                </Box>
              </Stack>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Recent sessions */}
      <Grid container spacing={2.5}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>Sesi AI Tutor Terbaru</Typography>
                <Button size="small" onClick={() => navigate('/tutor')} data-testid="dashboard-all-sessions-btn">Lihat semua</Button>
              </Stack>
              {sessions.length === 0 ? (
                <Typography color="text.secondary">
                  Belum ada sesi. Coba klik <b>Mulai Belajar dengan AI</b> di atas.
                </Typography>
              ) : (
                <Stack spacing={1.25}>
                  {sessions.slice(0, 5).map((s) => (
                    <Card key={s.session_uid} variant="outlined" sx={{ p: 1.5, cursor: 'pointer' }}
                      onClick={() => navigate(`/tutor/${s.session_uid}`)}
                      data-testid={`dashboard-session-${s.session_uid}`}>
                      <Typography sx={{ fontWeight: 600 }} noWrap>{s.title}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(s.updated_at).toLocaleString()}
                      </Typography>
                    </Card>
                  ))}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>Kuis Baru</Typography>
                <Button size="small" onClick={() => navigate('/quizzes')} data-testid="dashboard-all-quizzes-btn">Lihat semua</Button>
              </Stack>
              {quizzes.length === 0 ? (
                <Typography color="text.secondary">Belum ada kuis. {isTeacher && 'Buat kuis pertamamu!'}</Typography>
              ) : (
                <Stack spacing={1.25}>
                  {quizzes.slice(0, 5).map((q) => (
                    <Card key={q.id} variant="outlined" sx={{ p: 1.5 }}>
                      <Stack direction="row" alignItems="center" justifyContent="space-between">
                        <Box>
                          <Typography sx={{ fontWeight: 600 }} noWrap>{q.title}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {q.question_count} soal · {q.difficulty} · {q.source === 'system' ? 'AI-Generated' : 'Guru'}
                          </Typography>
                        </Box>
                        <Button size="small" variant="contained" onClick={() => navigate(`/quizzes/${q.id}/take`)}
                          data-testid={`dashboard-take-quiz-${q.id}-btn`}>
                          Kerjakan
                        </Button>
                      </Stack>
                    </Card>
                  ))}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
