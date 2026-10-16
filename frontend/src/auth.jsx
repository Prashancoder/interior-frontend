import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { authApi, getStoredToken, getStoredUser, storeSession } from './api'

const AuthContext = createContext(null)

export function homePathForRole(role) {
  if (role === 'seller') return '/seller/dashboard'
  if (role === 'admin') return '/admin/dashboard'
  return '/decor'
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getStoredToken())
  const [user, setUser] = useState(() => getStoredUser())
  const [ready, setReady] = useState(!getStoredToken())
  const [authError, setAuthError] = useState('')

  function applySession(nextToken, nextUser) {
    setToken(nextToken || '')
    setUser(nextUser || null)
    storeSession(nextToken, nextUser)
  }

  function logout() {
    applySession('', null)
  }

  useEffect(() => {
    function onUnauthorized() {
      logout()
    }
    window.addEventListener('decore:unauthorized', onUnauthorized)
    return () => window.removeEventListener('decore:unauthorized', onUnauthorized)
  }, [])

  useEffect(() => {
    let cancelled = false
    async function hydrate() {
      const existing = getStoredToken()
      if (!existing) {
        setReady(true)
        return
      }
      try {
        const profile = await authApi.me()
        if (!cancelled) {
          applySession(existing, profile)
          setAuthError('')
        }
      } catch {
        if (!cancelled) {
          applySession('', null)
        }
      } finally {
        if (!cancelled) setReady(true)
      }
    }
    hydrate()
    return () => {
      cancelled = true
    }
  }, [])

  async function login(payload) {
    const data = await authApi.login(payload)
    applySession(data.access_token, data.user)
    return data.user
  }

  async function register(payload) {
    const data = await authApi.register(payload)
    applySession(data.access_token, data.user)
    return data.user
  }

  const value = useMemo(
    () => ({
      token,
      user,
      ready,
      authError,
      setAuthError,
      login,
      register,
      logout,
      isAuthenticated: Boolean(token && user),
    }),
    [token, user, ready, authError]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
