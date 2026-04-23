import api from './api'

export const authService = {
  register: async (userData) => {
    const response = await api.post('/api/auth/register', userData)
    if (response.data?.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
    }
    return response.data
  },

  login: async (email, password) => {
    const response = await api.post('/api/auth/login', { email, password })
    if (response.data?.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
    }
    return response.data
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  },

  getCurrentUser: async () => {
    const response = await api.get('/api/users/me')
    return response.data
  },
}
