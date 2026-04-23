import api, { API_BASE_URL } from './api'

export const quizService = {
  list: async (course_id) => {
    const res = await api.get('/api/quizzes/', { params: course_id ? { course_id } : {} })
    return res.data
  },
  get: async (id) => (await api.get(`/api/quizzes/${id}`)).data,
  generate: async (payload) => (await api.post('/api/quizzes/generate', payload)).data,
  create: async (payload) => (await api.post('/api/quizzes/', payload)).data,
  remove: async (id) => {
    await api.delete(`/api/quizzes/${id}`)
  },
  submit: async (id, answers) =>
    (await api.post(`/api/quizzes/${id}/attempts`, { answers })).data,
  attempts: async (id) => (await api.get(`/api/quizzes/${id}/attempts`)).data,
  exportExcel: async (id) => {
    const token = localStorage.getItem('access_token')
    const resp = await fetch(`${API_BASE_URL}/api/quizzes/${id}/export`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!resp.ok) throw new Error('Gagal ekspor Excel')
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `hasil_kuis_${id}.xlsx`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  },
}
