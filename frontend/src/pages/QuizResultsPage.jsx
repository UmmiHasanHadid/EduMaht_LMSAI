import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box, Card, CardContent, Typography, Button, Stack, CircularProgress,
  Alert, Table, TableHead, TableRow, TableCell, TableBody, Chip,
} from '@mui/material'
import TableChartIcon from '@mui/icons-material/TableChart'
import { quizService } from '../services/quizService'

export default function QuizResultsPage() {
  const { quizId } = useParams()
  const navigate = useNavigate()
  const [quiz, setQuiz] = useState(null)
  const [attempts, setAttempts] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const [q, a] = await Promise.all([
          quizService.get(quizId),
          quizService.attempts(quizId),
        ])
        setQuiz(q); setAttempts(a)
      } catch (e) {
        setError(e.response?.data?.detail || 'Gagal memuat hasil')
      } finally { setLoading(false) }
    })()
  }, [quizId])

  if (loading) return <Box sx={{ display: 'grid', placeItems: 'center', py: 8 }}><CircularProgress /></Box>
  if (error) return <Alert severity="error">{error}</Alert>

  return (
    <Box data-testid="quiz-results-page">
      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" sx={{ fontWeight: 800 }}>{quiz?.title}</Typography>
          <Typography color="text.secondary">Rekap hasil pengerjaan</Typography>
        </Box>
        <Button startIcon={<TableChartIcon />} variant="contained"
          onClick={() => quizService.exportExcel(quizId)} data-testid="export-btn">
          Unduh Excel
        </Button>
      </Stack>

      <Card>
        <CardContent>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>#</TableCell>
                <TableCell>Siswa</TableCell>
                <TableCell align="right">Skor</TableCell>
                <TableCell align="right">%</TableCell>
                <TableCell>Waktu</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {attempts.length === 0 && (
                <TableRow><TableCell colSpan={5} align="center">Belum ada yang mengerjakan.</TableCell></TableRow>
              )}
              {attempts.map((a, i) => (
                <TableRow key={a.id} data-testid={`attempt-row-${a.id}`}>
                  <TableCell>{i + 1}</TableCell>
                  <TableCell>{a.student_name || `Siswa #${a.student_id}`}</TableCell>
                  <TableCell align="right">{a.score}/{a.max_score}</TableCell>
                  <TableCell align="right">
                    <Chip size="small" color={a.percentage >= 70 ? 'success' : a.percentage >= 50 ? 'warning' : 'error'}
                      label={`${a.percentage}%`} />
                  </TableCell>
                  <TableCell>{a.submitted_at ? new Date(a.submitted_at).toLocaleString() : '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Stack direction="row" justifyContent="flex-end" sx={{ mt: 2 }}>
        <Button onClick={() => navigate('/quizzes')}>Kembali</Button>
      </Stack>
    </Box>
  )
}
