"use client"

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { getToken, getStoredUser, clearToken, storeUser, getProfile, type User } from "@/lib/auth"

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (user: User, token: string) => void
  logout: () => void
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: () => {},
  logout: () => {},
  refresh: async () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const init = async () => {
      const token = getToken()
      if (!token) {
        setLoading(false)
        return
      }
      const stored = getStoredUser()
      if (stored) {
        setUser(stored)
        setLoading(false)
      }
      try {
        const fresh = await getProfile()
        setUser(fresh)
        storeUser(fresh)
      } catch {
        clearToken()
        setUser(null)
      }
      setLoading(false)
    }
    init()
  }, [])

  const login = (u: User, token: string) => {
    storeUser(u)
    setUser(u)
  }

  const logout = () => {
    clearToken()
    setUser(null)
  }

  const refresh = async () => {
    try {
      const fresh = await getProfile()
      setUser(fresh)
      storeUser(fresh)
    } catch {
      clearToken()
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
