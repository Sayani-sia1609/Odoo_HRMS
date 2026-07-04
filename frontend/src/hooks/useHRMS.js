import { useAuth } from '../context/AuthContext'

export function useHRMS() {
  return useAuth()
}
