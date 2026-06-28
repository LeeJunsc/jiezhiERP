import axios from 'axios'

export const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true
})

export interface Page<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export async function list<T>(url: string, params: Record<string, unknown> = {}) {
  const response = await api.get<Page<T>>(url, { params })
  return response.data
}

export async function create<T>(url: string, data: unknown) {
  const response = await api.post<T>(url, data)
  return response.data
}
