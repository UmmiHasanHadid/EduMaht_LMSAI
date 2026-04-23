import { create } from 'zustand'
import { authService } from '../services/authService'

export const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null })
    try {
      const data = await authService.login(email, password)
      set({ user: data.user, isAuthenticated: true, isLoading: false })
      return data
    } catch (error) {
      const msg = error.response?.data?.detail || error.message || 'Login gagal'
      set({ error: msg, isLoading: false })
      throw new Error(msg)
    }
  },

  register: async (userData) => {
    set({ isLoading: true, error: null })
    try {
      const data = await authService.register(userData)
      if (data?.user && data?.access_token) {
        set({ user: data.user, isAuthenticated: true, isLoading: false })
      } else {
        set({ isLoading: false })
      }
      return data
    } catch (error) {
      const detail = error.response?.data?.detail
      const msg = Array.isArray(detail)
        ? detail.map((d) => d.msg).join(', ')
        : (detail || error.message || 'Registrasi gagal')
      set({ error: msg, isLoading: false })
      throw new Error(msg)
    }
  },

  logout: () => {
    authService.logout()
    set({ user: null, isAuthenticated: false })
  },

  loadUser: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ user: null, isAuthenticated: false })
      return
    }
    try {
      const user = await authService.getCurrentUser()
      set({ user, isAuthenticated: true })
    } catch {
      authService.logout()
      set({ user: null, isAuthenticated: false })
    }
  },

  clearError: () => set({ error: null }),
}))
