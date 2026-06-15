"use client"

import { useEffect, type ReactNode } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/AuthContext"

interface Props {
  children: ReactNode
  roles?: string[]
  fallback?: ReactNode
}

export default function ProtectedRoute({ children, roles, fallback }: Props) {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (loading) return
    if (!user) {
      router.push("/login")
      return
    }
    if (roles && !roles.includes(user.role)) {
      router.push("/dashboard")
    }
  }, [user, loading, roles, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!user) return fallback ?? null
  if (roles && !roles.includes(user.role)) return fallback ?? null

  return <>{children}</>
}
