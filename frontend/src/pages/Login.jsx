import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Box, Card, TextField, Button, Typography, Alert, CircularProgress, Chip, Stack,
} from '@mui/material'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import { useAuthStore } from '../stores/authStore'

const DEMO = [
  { label: 'Siswa', email: 'siswa@edumaht.com', password: 'Siswa1234' },
  { label: 'Guru', email: 'guru@edumaht.com', password: 'Guru1234' },
  { label: 'Admin', email: 'admin@edumaht.com', password: 'Admin1234' },
]

export default function Login() {
  const navigate = useNavigate()
  const { login, isLoading, error, clearError } = useAuthStore()
  const [form, setForm] = useState({ email: '', password: '' })

  const submit = async (e) => {
    e.preventDefault()
    clearError()
    try {
      await login(form.email, form.password)
      navigate('/dashboard')
    } catch {
      /* error shown via store */
    }
  }

  const fillDemo = (d) => setForm({ email: d.email, password: d.password })

  return (
    <Box sx={{
      minHeight: '100vh', display: 'grid', placeItems: 'center', px: 2,
      background: 'radial-gradient(1200px 500px at 10% -10%, rgba(79,70,229,0.18), transparent 60%), radial-gradient(900px 500px at 110% 110%, rgba(245,158,11,0.18), transparent 60%)',
    }}>
      <Card sx={{ width: '100%', maxWidth: 440, p: { xs: 3, sm: 4 } }} data-testid="login-card">
        <Stack direction="row" spacing={1.25} alignItems="center" sx={{ mb: 3 }}>
          <AutoAwesomeIcon color="primary" />
          <Typography variant="h5" sx={{ fontWeight: 800 }}>
            EduMaht<Box component="span" sx={{ color: 'secondary.main', ml: 0.5 }}>·AI</Box>
          </Typography>
        </Stack>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>Selamat datang kembali</Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Masuk untuk belajar bersama AI Tutor <b>Bu Maht</b>.
        </Typography>

        {error && <Alert severity="error" sx={{ mb: 2 }} data-testid="login-error">{error}</Alert>}

        <Box component="form" onSubmit={submit}>
          <TextField
            fullWidth label="Email" type="email" margin="normal" required
            value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
            inputProps={{ 'data-testid': 'login-email-input' }}
          />
          <TextField
            fullWidth label="Password" type="password" margin="normal" required
            value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
            inputProps={{ 'data-testid': 'login-password-input' }}
          />
          <Button
            fullWidth type="submit" variant="contained" sx={{ mt: 2.5, py: 1.4 }}
            disabled={isLoading}
            data-testid="login-submit-btn"
          >
            {isLoading ? <CircularProgress size={22} /> : 'Masuk'}
          </Button>
        </Box>

        <Box sx={{ mt: 3 }}>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
            Coba akun demo:
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {DEMO.map((d) => (
              <Chip
                key={d.email}
                label={d.label}
                onClick={() => fillDemo(d)}
                clickable
                size="small"
                data-testid={`demo-${d.label.toLowerCase()}-chip`}
              />
            ))}
          </Stack>
        </Box>

        <Typography variant="body2" sx={{ textAlign: 'center', mt: 3 }}>
          Belum punya akun?{' '}
          <Link to="/register" style={{ textDecoration: 'none' }} data-testid="to-register-link">
            <b>Daftar di sini</b>
          </Link>
        </Typography>
      </Card>
    </Box>
  )
}
