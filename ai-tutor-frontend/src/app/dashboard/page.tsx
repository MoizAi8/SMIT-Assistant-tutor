"use client"

import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { ArrowLeft, GraduationCap, BookOpen, Users, FileCode, MessageSquare, Plus, Trash2, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import Link from "next/link"
import { useAuth } from "@/contexts/AuthContext"
import { authHeaders, requireAuth } from "@/lib/auth"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface SessionItem {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export default function DashboardPage() {
  const { user, loading } = useAuth()
  const [sessions, setSessions] = useState<SessionItem[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(true)

  useEffect(() => {
    if (!user) return
    loadSessions()
  }, [user])

  const loadSessions = async () => {
    setSessionsLoading(true)
    try {
      const token = requireAuth()
      const res = await fetch(`${API_BASE}/sessions`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        setSessions(await res.json())
      }
    } catch {} finally {
      setSessionsLoading(false)
    }
  }

  const createSession = async () => {
    try {
      const token = requireAuth()
      const res = await fetch(`${API_BASE}/sessions`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ title: `Chat ${new Date().toLocaleString()}` }),
      })
      if (res.ok) {
        loadSessions()
      }
    } catch {}
  }

  const deleteSession = async (id: string) => {
    try {
      const token = requireAuth()
      await fetch(`${API_BASE}/sessions/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      })
      loadSessions()
    } catch {}
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen pt-24 pb-16 flex items-center justify-center">
        <Card glass className="p-8 max-w-md mx-auto text-center">
          <GraduationCap className="w-12 h-12 text-primary mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-2">Login Required</h2>
          <p className="text-muted-foreground mb-6">Please login to access your dashboard.</p>
          <Link href="/login"><Button>Go to Login</Button></Link>
        </Card>
      </div>
    )
  }

  const statCards = [
    { label: "Role", value: user.role.charAt(0).toUpperCase() + user.role.slice(1), icon: Users, color: "text-blue-500" },
    { label: "Sessions", value: sessions.length.toString(), icon: MessageSquare, color: "text-green-500" },
    { label: "Display Name", value: user.display_name, icon: BookOpen, color: "text-purple-500" },
    { label: "Username", value: `@${user.username}`, icon: FileCode, color: "text-amber-500" },
  ]

  return (
    <div className="min-h-screen pt-24 pb-16">
      <div className="max-width px-6">
        <Link href="/"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Home
        </Link>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
          <h1 className="text-3xl md:text-4xl font-display font-bold">
            Welcome, <span className="text-gradient">{user.display_name}</span>
          </h1>
          <p className="text-muted-foreground mt-2">Role: <span className="text-foreground font-medium">{user.role}</span></p>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
          {statCards.map((stat, i) => (
            <motion.div key={stat.label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
              <Card glass className="p-5">
                <div className="flex items-center gap-3">
                  <div className={`${stat.color}`}>
                    <stat.icon className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">{stat.label}</p>
                    <p className="font-semibold text-sm">{stat.value}</p>
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>

        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-display font-semibold">Your Chat Sessions</h2>
          <Button size="sm" onClick={createSession} className="gap-2">
            <Plus className="w-3.5 h-3.5" /> New Session
          </Button>
        </div>

        {user.role === "admin" && (
          <div className="flex gap-3 mb-6">
            <Link href="/register">
              <Button variant="outline" size="sm" className="gap-2">
                <Users className="w-3.5 h-3.5" /> Register New User
              </Button>
            </Link>
          </div>
        )}

        <Card glass className="p-6">
          {sessionsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-12">
              <MessageSquare className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground">No chat sessions yet.</p>
              <Button variant="glass" size="sm" onClick={createSession} className="mt-4">
                Create your first session
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              {sessions.map((s) => (
                <div key={s.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-accent/50 transition-colors group">
                  <div className="flex items-center gap-3 min-w-0">
                    <MessageSquare className="w-4 h-4 text-muted-foreground shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{s.title}</p>
                      <p className="text-[10px] text-muted-foreground">
                        {s.message_count} messages · {new Date(s.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Link href={`/result?session=${s.id}`}>
                      <Button variant="ghost" size="sm" className="h-8 px-2 text-xs">Open</Button>
                    </Link>
                    <button onClick={() => deleteSession(s.id)} className="p-1.5 rounded-md hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition-colors">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
