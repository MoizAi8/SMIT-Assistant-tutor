"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { ArrowLeft, LogIn, Loader2, User, Lock, GraduationCap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import Link from "next/link"
import { login as apiLogin } from "@/lib/auth"
import { useAuth } from "@/contexts/AuthContext"

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password.trim()) {
      setError("Please enter username and password")
      return
    }
    setLoading(true)
    setError("")
    try {
      const data = await apiLogin(username, password)
      login(data.user, data.token)
      router.push( data.user.role === "admin" ? "/dashboard" : "/grade")
    } catch (err: any) {
      setError(err.message || "Login failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen pt-24 pb-16 flex items-center justify-center">
      <div className="max-width px-6 w-full">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-md mx-auto"
        >
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center mx-auto mb-4">
              <GraduationCap className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-display font-bold">Welcome Back</h1>
            <p className="text-muted-foreground mt-2">Login to SMIT ASSISTANT TUTOR</p>
          </div>

          <Card glass className="p-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-500"
                >
                  {error}
                </motion.div>
              )}

              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                  Username
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter username"
                    className="w-full bg-transparent border border-border rounded-lg pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                    className="w-full bg-transparent border border-border rounded-lg pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors"
                  />
                </div>
              </div>

              <Button type="submit" size="xl" disabled={loading} className="w-full">
                {loading ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" /> Logging in...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <LogIn className="w-4 h-4" /> Login
                  </span>
                )}
              </Button>
            </form>

            <div className="mt-6 pt-4 border-t border-border/30">
              <p className="text-xs text-muted-foreground text-center mb-3">Demo accounts</p>
              <div className="grid grid-cols-3 gap-2 text-[10px]">
                <div className="p-2 rounded-lg bg-primary/5 border border-border/30 text-center">
                  <p className="font-medium text-foreground">admin</p>
                  <p className="text-muted-foreground">admin123</p>
                </div>
                <div className="p-2 rounded-lg bg-primary/5 border border-border/30 text-center">
                  <p className="font-medium text-foreground">teacher</p>
                  <p className="text-muted-foreground">teacher123</p>
                </div>
                <div className="p-2 rounded-lg bg-primary/5 border border-border/30 text-center">
                  <p className="font-medium text-foreground">student</p>
                  <p className="text-muted-foreground">student123</p>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
