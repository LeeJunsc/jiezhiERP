import { defineStore } from 'pinia'
import { api } from '../api/client'

interface User {
  id: number
  username: string
  first_name: string
  is_superuser: boolean
  groups: Array<{ id: number; name: string }>
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null
  }),
  actions: {
    async login(username: string, password: string) {
      const response = await api.post<User>('/auth/login', { username, password })
      this.user = response.data
    },
    async loadMe() {
      try {
        const response = await api.get<User>('/auth/me')
        this.user = response.data
      } catch {
        this.user = null
      }
    },
    async logout() {
      await api.post('/auth/logout')
      this.user = null
    }
  }
})
