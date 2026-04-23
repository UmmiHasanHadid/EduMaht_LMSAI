import { useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'

import { lightTheme, darkTheme } from './themes/theme'
import { useAuthStore } from './stores/authStore'

import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import AITutorPage from './pages/AITutorPage'
import QuizzesPage from './pages/QuizzesPage'
import QuizTakePage from './pages/QuizTakePage'
import QuizResultsPage from './pages/QuizResultsPage'
import Layout from './components/Layout'

function ProtectedRoute({ children, ready, isAuthenticated }) {
  if (!ready) {
    return (
      <Box sx={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
        <CircularProgress />
      </Box>
    )
  }
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default function App() {
  const { isAuthenticated, loadUser } = useAuthStore()
  const [ready, setReady] = useState(false)
  const [isDarkMode, setIsDarkMode] = useState(() => localStorage.getItem('theme') === 'dark')

  useEffect(() => {
    loadUser().finally(() => setReady(true))
  }, [])

  useEffect(() => {
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light')
  }, [isDarkMode])

  return (
    <ThemeProvider theme={isDarkMode ? darkTheme : lightTheme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route
            element={
              <ProtectedRoute ready={ready} isAuthenticated={isAuthenticated}>
                <Layout isDarkMode={isDarkMode} onToggleDarkMode={() => setIsDarkMode((v) => !v)} />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/tutor" element={<AITutorPage />} />
            <Route path="/tutor/:sessionUid" element={<AITutorPage />} />
            <Route path="/quizzes" element={<QuizzesPage />} />
            <Route path="/quizzes/:quizId/take" element={<QuizTakePage />} />
            <Route path="/quizzes/:quizId/results" element={<QuizResultsPage />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </ThemeProvider>
  )
}
