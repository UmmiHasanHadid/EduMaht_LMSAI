import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Box, Card, TextField, Button, Typography, Alert, CircularProgress,
  FormControl, InputLabel, Select, MenuItem, Stack,
} from '@mui/material'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import { useAuthStore } from '../stores/authStore'

export default function Register() {
  const navigate = useNavigate()
  const { register, isLoading, error, clearError } = useAuthStore()
  const [form, setForm] = useState({
    email: '', username: '', full_name: '', password: '', confirm: '', role: 'student',
  })
  const [localErr, setLocalErr] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    clearError()
    setLocalErr('')
    if (form.password !== form.confirm) {
      setLocalErr('Konfirmasi password tidak cocok')
      return
    }
    if (form.password.length < 6) {
      setLocalErr('Password minimal 6 karakter')
      return
    }
    try {
      const res = await register({
        email: form.email,
        username: form.username,
        full_name: form.full_name,
        password: form.password,
        role: form.role,
      })
      if (res?.user && res?.access_token) {
        navigate('/dashboard')
      } else {
        navigate('/login')
      }
    } catch { /* error shown */ }
  }

  const change = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  return (
    <Box sx={{
      minHeight: '100vh', display: 'grid', placeItems: 'center', px: 2, py: 4,
      background: 'radial-gradient(1000px 500px at 120% 0%, rgba(245,158,11,0.18), transparent 60%), radial-gradient(900px 600px at -10% 110%, rgba(79,70,229,0.18), transparent 60%)',
    }}>
      <Card sx={{ width: '100%', maxWidth: 520, p: { xs: 3, sm: 4 } }} data-testid="register-card">
        <Stack direction="row" spacing={1.25} alignItems="center" sx={{ mb: 3 }}>
          <AutoAwesomeIcon color="primary" />
          <Typography variant="h5" sx={{ fontWeight: 800 }}>
            EduMaht<Box component="span" sx={{ color: 'secondary.main', ml: 0.5 }}>·AI</Box>
          </Typography>
        </Stack>
        <Typography variant="h4" sx={{ fontWeight: 800 }}>Buat akun baru</Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Gratis & siap dipakai siswa serta guru.
        </Typography>

        {(error || localErr) && (
          <Alert severity="error" sx={{ mb: 2 }} data-testid="register-error">{localErr || error}</Alert>
        )}

        <Box component="form" onSubmit={submit}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField fullWidth label="Nama Lengkap" required value={form.full_name}
              onChange={change('full_name')} inputProps={{ 'data-testid': 'register-fullname-input' }}/>
            <TextField fullWidth label="Username" required value={form.username}
              onChange={change('username')} inputProps={{ 'data-testid': 'register-username-input' }}/>
          </Stack>
          <TextField fullWidth label="Email" type="email" required margin="normal"
            value={form.email} onChange={change('email')} inputProps={{ 'data-testid': 'register-email-input' }}/>
          <FormControl fullWidth margin="normal">
            <InputLabel>Peran</InputLabel>
            <Select value={form.role} label="Peran" onChange={change('role')}
              data-testid="register-role-select">
              <MenuItem value="student">Siswa</MenuItem>
              <MenuItem value="instructor">Guru</MenuItem>
            </Select>
          </FormControl>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField fullWidth label="Password" type="password" required value={form.password}
              onChange={change('password')} inputProps={{ 'data-testid': 'register-password-input' }}/>
            <TextField fullWidth label="Konfirmasi Password" type="password" required value={form.confirm}
              onChange={change('confirm')} inputProps={{ 'data-testid': 'register-confirm-input' }}/>
          </Stack>
          <Button fullWidth type="submit" variant="contained" sx={{ mt: 3, py: 1.4 }}
            disabled={isLoading} data-testid="register-submit-btn">
            {isLoading ? <CircularProgress size={22} /> : 'Daftar'}
          </Button>
        </Box>

        <Typography variant="body2" sx={{ textAlign: 'center', mt: 3 }}>
          Sudah punya akun?{' '}
          <Link to="/login" style={{ textDecoration: 'none' }} data-testid="to-login-link">
            <b>Masuk di sini</b>
          </Link>
        </Typography>
      </Card>
    </Box>
  )
}
