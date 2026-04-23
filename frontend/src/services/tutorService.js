import api, { API_BASE_URL } from './api'

export const tutorService = {
  chat: async ({ message, session_uid, course_id, lesson_id }) => {
    const res = await api.post('/api/ai/tutor/chat', {
      message,
      session_uid,
      course_id,
      lesson_id,
    })
    return res.data
  },
  listSessions: async () => {
    const res = await api.get('/api/ai/tutor/sessions')
    return res.data
  },
  getMessages: async (session_uid) => {
    const res = await api.get(`/api/ai/tutor/sessions/${session_uid}/messages`)
    return res.data
  },
  deleteSession: async (session_uid) => {
    await api.delete(`/api/ai/tutor/sessions/${session_uid}`)
  },
  downloadUrl: (session_uid) => {
    const token = localStorage.getItem('access_token')
    // Direct link with auth via query token is not used; we use fetch with header and blob
    return async () => {
      const resp = await fetch(
        `${API_BASE_URL}/api/ai/tutor/sessions/${session_uid}/download`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (!resp.ok) throw new Error('Gagal mengunduh')
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `tutor-${session_uid.slice(0, 8)}.txt`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    }
  },
  explain: async (payload) => {
    const res = await api.post('/api/ai/tutor/explain', payload)
    return res.data
  },
  summarize: async (material, target_length = 'ringkas') => {
    const res = await api.post('/api/ai/tutor/summarize', { material, target_length })
    return res.data
  },
  retentionNotice: async () => {
    const res = await api.get('/api/ai/tutor/retention-notice')
    return res.data
  },
}
