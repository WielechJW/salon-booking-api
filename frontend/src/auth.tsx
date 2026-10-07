import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  api,
  getAccessToken,
  getMe,
  setAccessToken,
  SESSION_EXPIRED_EVENT,
  unwrap,
  type User,
} from '@/lib/api/client'
import { queryClient } from '@/lib/query'

type Auth = {
  user: User | undefined
  loading: boolean
  expired: boolean
  error: Error | null
  retry: () => unknown
  login: (email: string, password: string) => Promise<User>
  logout: () => void
}
const AuthContext = createContext<Auth | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState(getAccessToken)
  const [expired, setExpired] = useState(false)
  const profile = useQuery({
    queryKey: ['me'],
    queryFn: ({ signal }) => getMe(signal),
    enabled: !!token,
    retry: false,
    staleTime: 60_000,
  })

  const clearSession = useCallback((expiredSession = false) => {
    setAccessToken(null)
    setToken(null)
    setExpired(expiredSession)
    void queryClient.cancelQueries()
    queryClient.clear()
  }, [])

  useEffect(() => {
    const handler = () => clearSession(true)
    window.addEventListener(SESSION_EXPIRED_EVENT, handler)
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, handler)
  }, [clearSession])

  useEffect(() => {
    if (!token) return
    try {
      const payload = JSON.parse(
        atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')),
      ) as { exp: number }
      const timeout = window.setTimeout(
        () => window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT)),
        Math.max(0, payload.exp * 1000 - Date.now()),
      )
      return () => window.clearTimeout(timeout)
    } catch {
      window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
    }
  }, [token])

  async function login(email: string, password: string) {
    const response = unwrap(
      await api.POST('/auth/login', {
        body: { username: email, password, scope: '' },
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        bodySerializer: (body) =>
          new URLSearchParams({
            username: body.username,
            password: body.password,
            scope: body.scope,
          }).toString(),
      }),
    )
    await queryClient.cancelQueries()
    queryClient.clear()
    setAccessToken(response.access_token)
    try {
      const user = await getMe()
      queryClient.setQueryData(['me'], user)
      setToken(response.access_token)
      setExpired(false)
      return user
    } catch (error) {
      clearSession()
      throw error
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user: token ? profile.data : undefined,
        loading: !!token && profile.isPending,
        expired,
        error: token ? profile.error : null,
        retry: profile.refetch,
        login,
        logout: () => clearSession(),
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('AuthProvider is required')
  return auth
}

export function safeReturnTo(value: string | null) {
  return value?.startsWith('/') &&
    !value.startsWith('//') &&
    !value.includes('\\') &&
    !/^\/(login|register)([/?#]|$)/.test(value)
    ? value
    : '/account'
}
