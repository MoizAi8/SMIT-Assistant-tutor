"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { useAuth } from "@/contexts/AuthContext"
import { register as apiRegister } from "@/lib/auth"
import { ArrowLeft, Loader2, UserPlus } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"

const ROLES = ["student", "teacher", "admin"]

export default function RegisterPage() {
  const { user } = useAuth()
  const router = useRouter()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [role, setRole] = useState("student")
  const [displayName, setDisplayName] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  if (!user || user.role !== "admin") {
    return (
      <div className="min-h-screen pt-24 pb-16 flex items-center justify-center">
        <Card glass className="p-8 max-w-md mx-auto text-center">
          <p className="text-muted-foreground mb-4">Only admins can register new users.</p>
          <Link href="/dashboard"><Button>Go to Dashboard</Button></Link>
        </Card>
      </div>
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password.trim()) {
      setError("Username and password required")
      return
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters")
      return
    }
    setLoading(true)
    setError("")
    setSuccess("")
    try {
      await apiRegister(username, password, role, displayName)
      setSuccess(`User "${username}" created as ${role}`)
      setUsername("")
      setPassword("")
      setDisplayName("")
    } catch (err: any) {
      setError(err.message || "Registration failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen pt-24 pb-16 flex items-center justify-center">
      <div className="max-width px-6 w-full">
        <Link href="/dashboard"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="max-w-md mx-auto"
        >
          <h1 className="text-2xl font-display font-bold mb-6 text-center">Register New User</h1>
          <Card glass className="p-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-500">{error}</div>
              )}
              {success && (
                <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-sm text-green-500">{success}</div>
              )}
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Username</label>
                <input value={username} onChange={(e) => setUsername(e.target.value)}
                  placeholder="Username" required
                  className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Password</label>
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min 6 characters" required
                  className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Display Name</label>
                <input value={displayName} onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Optional friendly name"
                  className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Role</label>
                <div className="flex gap-2">
                  {ROLES.map((r) => (
                    <button key={r} type="button" onClick={() => setRole(r)}
                      className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium border transition-all ${
                        role === r
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {r.charAt(0).toUpperCase() + r.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
              <Button type="submit" disabled={loading} className="w-full">
                {loading ? (
                  <span className="flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Creating...</span>
                ) : (
                  <span className="flex items-center gap-2"><UserPlus className="w-4 h-4" /> Create User</span>
                )}
              </Button>
            </form>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
