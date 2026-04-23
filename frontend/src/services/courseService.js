import api from './api'

export const courseService = {
  getCourses: async (params = {}) => {
    const response = await api.get('/api/courses', { params })
    return response.data
  },

  getCourseById: async (id) => {
    const response = await api.get(`/api/courses/${id}`)
    return response.data
  },

  createCourse: async (courseData) => {
    const response = await api.post('/api/courses', courseData)
    return response.data
  },

  updateCourse: async (id, courseData) => {
    const response = await api.put(`/api/courses/${id}`, courseData)
    return response.data
  },

  deleteCourse: async (id) => {
    await api.delete(`/api/courses/${id}`)
  },

  enrollCourse: async (courseId) => {
    const response = await api.post('/api/enrollments', { course_id: courseId })
    return response.data
  },

  getMyCourses: async () => {
    const response = await api.get('/api/enrollments/my-courses')
    return response.data
  },
}
