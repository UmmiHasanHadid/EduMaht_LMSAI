/* AI Tutor chat page with multi-turn history, session list sidebar,
   retention reminder, .txt download, delete, and Markdown rendering. */
import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Box, Grid, Card, CardContent, Typography, TextField, IconButton, Button,
  Stack, Alert, Chip, Avatar, CircularProgress, Divider, Tooltip, Dialog,
  DialogTitle, DialogContent, DialogActions,
} from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import AddCircleIcon from '@mui/icons-material/AddCircle'
import DownloadIcon from '@mui/icons-material/Download'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import PersonIcon from '@mui/icons-material/Person'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { tutorService } from '../services/tutorService'
import { useAuthStore } from '../stores/authStore'

function Bubble({ role, content }) {
  const isUser = role === 'user'
  return (
    <Stack direction="row" spacing={1.25} sx={{
      justifyContent: isUser ? 'flex-end' : 'flex-start', mb: 1.5,
    }}>
      {!isUser && (
        <Avatar sx={{ bgcolor: 'primary.main', width: 34, height: 34 }}><SmartToyIcon fontSize="small" /></Avatar>
      )}
      <Box
        data-testid={`chat-msg-${role}`}
        sx={{
          maxWidth: { xs: '88%', md: '72%' },
          px: 2, py: 1.25,
          borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
          bgcolor: isUser ? 'primary.main' : 'background.paper',
          color: isUser ? 'primary.contrastText' : 'text.primary',
          boxShadow: isUser ? '0 6px 16px -10px rgba(79,70,229,0.5)' : '0 6px 16px -12px rgba(15,23,42,0.25)',
          border: isUser ? 'none' : (t) => `1px solid ${t.palette.divider}`,
        }}
        className={isUser ? '' : 'prose'}
      >
        {isUser ? (
          <Typography sx={{ whiteSpace: 'pre-wrap' }}>{content}</Typography>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        )}
      </Box>
      {isUser && (
        <Avatar sx={{ bgcolor: 'secondary.main', width: 34, height: 34, color: '#1F2937' }}><PersonIcon fontSize="small" /></Avatar>
      )}
    </Stack>
  )
}

export default function AITutorPage() {
  const { sessionUid } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()

  const [sessions, setSessions] = useState([])
  const [retention, setRetention] = useState(10)
  const [current, setCurrent] = useState(null)   // { session_uid, title, messages: [] }
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [noticeOpen, setNoticeOpen] = useState(false)
  const [noticeText, setNoticeText] = useState('')
  const bottomRef = useRef(null)

  const isTeacher = user?.role === 'instructor' || user?.role === 'admin'

  const loadSessions = async () => {
    try {
      const s = await tutorService.listSessions()
      setSessions(s.sessions || [])
      setRetention(s.retention_days || 10)
    } catch (e) {
      setError(e.response?.data?.detail || 'Gagal memuat sesi')
    }
  }

  const loadMessages = async (uid) => {
    try {
      const r = await tutorService.getMessages(uid)
      setCurrent({
        session_uid: uid,
        title: r.session.title,
        messages: r.messages,
      })
    } catch (e) {
      setError(e.response?.data?.detail || 'Gagal memuat pesan')
    }
  }

  useEffect(() => { loadSessions() }, [])

  useEffect(() => {
    if (sessionUid) loadMessages(sessionUid)
    else setCurrent({ session_uid: null, title: 'Sesi Baru', messages: [] })
  }, [sessionUid])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [current?.messages?.length, loading])

  useEffect(() => {
    // If teacher, show retention reminder once per mount
    if (isTeacher) {
      tutorService.retentionNotice().then((n) => {
        if (n?.is_teacher) {
          setNoticeText(n.message)
          setNoticeOpen(true)
        }
      }).catch(() => {})
    }
  }, [isTeacher])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setError('')
    setInput('')
    setLoading(true)
    // optimistic append
    setCurrent((c) => ({
      ...(c || { messages: [] }),
      messages: [...((c && c.messages) || []), { role: 'user', content: text, created_at: new Date().toISOString() }],
    }))
    try {
      const res = await tutorService.chat({
        message: text,
        session_uid: current?.session_uid || undefined,
      })
      setCurrent((c) => ({
        session_uid: res.session_uid,
        title: c?.title || text.slice(0, 60),
        messages: [...((c && c.messages) || []), { role: 'assistant', content: res.reply, created_at: res.created_at }],
      }))
      if (!current?.session_uid) {
        // update URL so refresh keeps this session
        navigate(`/tutor/${res.session_uid}`, { replace: true })
      }
      loadSessions()
    } catch (e) {
      setError(e.response?.data?.detail || 'AI Tutor tidak merespons, coba lagi sebentar.')
    } finally {
      setLoading(false)
    }
  }

  const startNew = () => {
    setCurrent({ session_uid: null, title: 'Sesi Baru', messages: [] })
    navigate('/tutor')
  }

  const removeSession = async (uid) => {
    await tutorService.deleteSession(uid)
    if (current?.session_uid === uid) startNew()
    loadSessions()
  }

  const download = async (uid) => {
    const fn = tutorService.downloadUrl(uid)
    try { await fn() } catch (e) { setError(String(e.message || e)) }
  }

  const messages = current?.messages || []

  return (
    <Box data-testid="ai-tutor-page">
      <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 2 }}>
        <SmartToyIcon color="primary" sx={{ fontSize: 32 }} />
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" sx={{ fontWeight: 800 }}>AI Tutor — Bu Maht</Typography>
          <Typography color="text.secondary">
            Model Gemini · Retensi otomatis {retention} hari · Privat & hanya untuk Anda
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<AddCircleIcon />} onClick={startNew} data-testid="new-session-btn">
          Sesi Baru
        </Button>
      </Stack>

      <Alert
        severity="info"
        icon={<InfoOutlinedIcon />}
        sx={{ mb: 2 }}
        data-testid="retention-banner"
      >
        Percakapan Anda tersimpan otomatis hingga <b>{retention} hari</b>, lalu dihapus.
        {isTeacher ? ' Sebagai guru, Anda tidak dapat melihat/unduh percakapan siswa.' : ' Guru tidak dapat melihat percakapan Anda.'}
      </Alert>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')} data-testid="chat-error">{error}</Alert>}

      <Grid container spacing={2.5}>
        <Grid item xs={12} md={4} lg={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1.5, fontWeight: 700 }}>
                SESI SAYA
              </Typography>
              {sessions.length === 0 && (
                <Typography variant="body2" color="text.secondary">Belum ada sesi.</Typography>
              )}
              <Stack spacing={1}>
                {sessions.map((s) => {
                  const active = s.session_uid === current?.session_uid
                  return (
                    <Card
                      variant="outlined"
                      key={s.session_uid}
                      data-testid={`session-item-${s.session_uid}`}
                      sx={{
                        p: 1.25, cursor: 'pointer',
                        borderColor: active ? 'primary.main' : undefined,
                        bgcolor: active ? 'action.hover' : 'transparent',
                      }}
                      onClick={() => navigate(`/tutor/${s.session_uid}`)}
                    >
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <Typography sx={{ fontWeight: 600, flex: 1 }} noWrap>{s.title}</Typography>
                      </Stack>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(s.updated_at).toLocaleString()}
                      </Typography>
                      <Stack direction="row" spacing={0.5} sx={{ mt: 0.75 }}>
                        <Tooltip title="Unduh (.txt)">
                          <IconButton size="small" onClick={(e) => { e.stopPropagation(); download(s.session_uid) }}
                            data-testid={`download-session-${s.session_uid}-btn`}>
                            <DownloadIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Hapus">
                          <IconButton size="small" color="error"
                            onClick={(e) => { e.stopPropagation(); removeSession(s.session_uid) }}
                            data-testid={`delete-session-${s.session_uid}-btn`}>
                            <DeleteOutlineIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </Card>
                  )
                })}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8} lg={9}>
          <Card sx={{ display: 'flex', flexDirection: 'column', height: { xs: '65vh', md: 'calc(100vh - 260px)' } }}>
            <Box sx={{ px: 2, py: 1.25, borderBottom: (t) => `1px solid ${t.palette.divider}` }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Chip size="small" color="primary" label={current?.session_uid ? 'Percakapan' : 'Mulai percakapan baru'} />
                <Typography sx={{ fontWeight: 700 }} noWrap>{current?.title || 'Sesi Baru'}</Typography>
              </Stack>
            </Box>

            <Box sx={{ flex: 1, overflowY: 'auto', px: { xs: 1.5, md: 3 }, py: 2.5 }} data-testid="chat-scroll-area">
              {messages.length === 0 && (
                <Box sx={{ textAlign: 'center', pt: 6, color: 'text.secondary' }}>
                  <SmartToyIcon sx={{ fontSize: 72, color: 'primary.main', opacity: 0.6 }} />
                  <Typography variant="h6" sx={{ mt: 1, fontWeight: 700 }}>Halo! Saya Bu Maht 👋</Typography>
                  <Typography>Tanyakan apa saja — dari matematika, sains, bahasa, hingga tips belajar.</Typography>
                </Box>
              )}
              {messages.map((m, i) => <Bubble key={i} role={m.role} content={m.content} />)}
              {loading && (
                <Stack direction="row" spacing={1} alignItems="center" sx={{ ml: 6, my: 1 }}>
                  <CircularProgress size={18} />
                  <Typography variant="caption" color="text.secondary">Bu Maht sedang mengetik…</Typography>
                </Stack>
              )}
              <div ref={bottomRef} />
            </Box>

            <Divider />
            <Box sx={{ p: 1.5 }}>
              <Stack direction="row" spacing={1}>
                <TextField
                  fullWidth placeholder="Tulis pertanyaanmu… (Enter untuk kirim, Shift+Enter untuk baris baru)"
                  multiline maxRows={5} value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
                  }}
                  disabled={loading}
                  inputProps={{ 'data-testid': 'chat-input' }}
                />
                <IconButton color="primary" onClick={send} disabled={loading || !input.trim()}
                  sx={{ width: 52, height: 52, bgcolor: 'primary.main', color: '#fff', '&:hover': { bgcolor: 'primary.dark' }, '&.Mui-disabled': { bgcolor: 'action.disabledBackground', color: 'text.disabled' } }}
                  data-testid="chat-send-btn">
                  {loading ? <CircularProgress size={22} sx={{ color: '#fff' }} /> : <SendIcon />}
                </IconButton>
              </Stack>
            </Box>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={noticeOpen} onClose={() => setNoticeOpen(false)}>
        <DialogTitle sx={{ fontWeight: 700 }}>Pengingat untuk Guru</DialogTitle>
        <DialogContent>
          <Typography>{noticeText}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNoticeOpen(false)} variant="contained" data-testid="notice-close-btn">Saya mengerti</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
