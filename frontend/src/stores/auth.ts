import { defineStore } from 'pinia'
import { api } from '../api/client'

interface User {
  id: number
  username: string
  first_name: string
  is_superuser: boolean
  groups: Array<{ id: number; name: string }>
  effective_permission_codes: string[]
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null
  }),
  getters: {
    permissionCodes: (state) => state.user?.effective_permission_codes || [],
    hasPermission: (state) => {
      return (code: string) => Boolean(
        state.user?.is_superuser ||
        state.user?.effective_permission_codes?.includes('*') ||
        state.user?.effective_permission_codes?.includes(code)
      )
    },
    hasAnyPermission: (state) => {
      return (codes: string[]) => Boolean(
        state.user?.is_superuser ||
        state.user?.effective_permission_codes?.includes('*') ||
        codes.some((code) => state.user?.effective_permission_codes?.includes(code))
      )
    }
  },
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
