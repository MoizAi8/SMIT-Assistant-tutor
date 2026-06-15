"use client"

import { useEffect, useState, useRef } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import {
  ArrowLeft, CheckCircle2, AlertCircle, Lightbulb, Code2,
  Send, Bot, User, Copy, Check, Loader2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import Link from "next/link"
import { getToken } from "@/lib/auth"

interface GradeResult {
  score: string
  verdict: string
  what_went_well: string[]
  major_issues: string[]
  explanation: string
  suggested_improvements: string[]
  corrected_code: string
}

export default function ResultPage() {
  const router = useRouter()
  const [grade, setGrade] = useState<GradeResult | null>(null)
  const [chatMessages, setChatMessages] = useState<{ role: string; text: string }[]>([])
  const [chatInput, setChatInput] = useState("")
  const [chatLoading, setChatLoading] = useState(false)
  const [sessionId, setSessionId] = useState("")
  const [copied, setCopied] = useState(false)
  const [tab, setTab] = useState<"feedback" | "code" | "chat">("feedback")
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const stored = sessionStorage.getItem("lastGrade")
    if (!stored) {
      router.push("/grade")
      return
    }
    setGrade(JSON.parse(stored))
    setSessionId(`session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`)

    setChatMessages([
      {
        role: "bot",
        text: "Assalam-o-Alaikum! Main aapki grading detail samjha sakta hoon. Koi sawaal hai? Jaise: 'Mujhe yeh issue samajh nahi aaya' ya 'Kaise improve karoon isko?'",
      },
    ])
  }, [router])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [chatMessages])

  const handleChat = async () => {
    if (!chatInput.trim() || chatLoading) return
    const msg = chatInput.trim()
    setChatInput("")
    setChatMessages((prev) => [...prev, { role: "user", text: msg }])
    setChatLoading(true)

    try {
      const token = getToken()
      const headers: Record<string, string> = { "Content-Type": "application/json" }
      if (token) headers["Authorization"] = `Bearer ${token}`

      const res = await fetch("/api/chat", {
        method: "POST",
        headers,
        body: JSON.stringify({
          session_id: sessionId,
          message: msg,
          grade_context: grade ? {
            score: grade.score,
            verdict: grade.verdict,
            explanation: grade.explanation,
            what_went_well: grade.what_went_well,
            major_issues: grade.major_issues,
          } : null,
        }),
      })
      const data = await res.json()
      setChatMessages((prev) => [...prev, { role: "bot", text: data.response }])
    } catch {
      setChatMessages((prev) => [
        ...prev,
        { role: "bot", text: "Mujhe maaf karein, main abhi jawab nahi de sakta. Backend server check karein." },
      ])
    } finally {
      setChatLoading(false)
    }
  }

  const copyCode = () => {
    if (!grade) return
    navigator.clipboard.writeText(grade.corrected_code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const parseScore = (s: string) => {
    const parts = s.split("/")
    return { num: parseInt(parts[0]) || 0, den: parseInt(parts[1]) || 100 }
  }

  if (!grade) return null

  const score = parseScore(grade.score)
  const pct = (score.num / score.den) * 100

  const getGradeColor = () => {
    if (pct >= 80) return "text-green-500"
    if (pct >= 60) return "text-amber-500"
    return "text-red-500"
  }

  return (
    <div className="min-h-screen pt-24 pb-16">
      <div className="max-width px-6">
        <Link
          href="/grade"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Grade Another
        </Link>

        {/* Score Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 100, delay: 0.2 }}
            className={`text-7xl md:text-8xl font-display font-bold ${getGradeColor()} mb-4`}
          >
            {grade.score}
          </motion.div>
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium border border-primary/20 bg-primary/5 text-primary mb-4">
            {grade.verdict}
          </span>
          <p className="text-muted-foreground max-w-xl mx-auto">{grade.explanation}</p>
        </motion.div>

        {/* Score Bar */}
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: "100%" }}
          className="max-w-md mx-auto mb-12"
        >
          <div className="h-2 rounded-full bg-muted overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${pct}%` }}
              transition={{ duration: 1, delay: 0.5 }}
              className={`h-full rounded-full ${pct >= 80 ? "bg-green-500" : pct >= 60 ? "bg-amber-500" : "bg-red-500"}`}
            />
          </div>
        </motion.div>

        {/* Tabs */}
        <div className="flex gap-2 mb-8 justify-center">
          {[
            { key: "feedback", label: "Feedback" },
            { key: "code", label: "Corrected Code" },
            { key: "chat", label: "Chat" },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key as typeof tab)}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-all ${
                tab === t.key
                  ? "bg-primary text-primary-foreground"
                  : "glass text-muted-foreground hover:text-foreground"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {tab === "feedback" && (
            <motion.div
              key="feedback"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="grid grid-cols-1 lg:grid-cols-2 gap-6"
            >
              <Card glass className="p-6">
                <h3 className="flex items-center gap-2 font-semibold mb-4 text-sm uppercase tracking-wider text-muted-foreground">
                  <CheckCircle2 className="w-4 h-4 text-green-500" /> What Went Well
                </h3>
                <ul className="space-y-3">
                  {grade.what_went_well.map((item, i) => (
                    <motion.li
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="flex items-start gap-3 text-sm"
                    >
                      <span className="text-green-500 mt-0.5">+</span>
                      {item}
                    </motion.li>
                  ))}
                </ul>
              </Card>

              <Card glass className="p-6">
                <h3 className="flex items-center gap-2 font-semibold mb-4 text-sm uppercase tracking-wider text-muted-foreground">
                  <AlertCircle className="w-4 h-4 text-amber-500" /> Major Issues
                </h3>
                <ul className="space-y-3">
                  {grade.major_issues.map((item, i) => (
                    <motion.li
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="flex items-start gap-3 text-sm"
                    >
                      <span className="text-amber-500 mt-0.5">!</span>
                      {item}
                    </motion.li>
                  ))}
                </ul>
              </Card>

              <Card glass className="p-6 lg:col-span-2">
                <h3 className="flex items-center gap-2 font-semibold mb-4 text-sm uppercase tracking-wider text-muted-foreground">
                  <Lightbulb className="w-4 h-4 text-primary" /> Suggested Improvements
                </h3>
                <ul className="space-y-2">
                  {grade.suggested_improvements.map((item, i) => (
                    <motion.li
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="flex items-start gap-3 text-sm"
                    >
                      <span className="text-primary mt-0.5">→</span>
                      {item}
                    </motion.li>
                  ))}
                </ul>
              </Card>
            </motion.div>
          )}

          {tab === "code" && (
            <motion.div
              key="code"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <Card glass className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="flex items-center gap-2 font-semibold text-sm uppercase tracking-wider text-muted-foreground">
                    <Code2 className="w-4 h-4 text-primary" /> Corrected Code
                  </h3>
                  <Button variant="ghost" size="sm" onClick={copyCode} className="gap-2">
                    {copied ? (
                      <><Check className="w-3 h-3" /> Copied</>
                    ) : (
                      <><Copy className="w-3 h-3" /> Copy</>
                    )}
                  </Button>
                </div>
                <pre className="p-4 rounded-lg bg-black/20 dark:bg-white/5 overflow-x-auto text-sm font-mono leading-relaxed">
                  <code>{grade.corrected_code}</code>
                </pre>
              </Card>
            </motion.div>
          )}

          {tab === "chat" && (
            <motion.div
              key="chat"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="max-w-2xl mx-auto"
            >
              <Card glass className="p-6">
                <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border/30">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 p-2">
                    <Bot className="w-full h-full text-white" />
                  </div>
                  <div>
                    <p className="font-semibold text-sm">Teaching Assistant</p>
                    <p className="text-xs text-muted-foreground">Ask me about your grade</p>
                  </div>
                </div>

                <div className="space-y-3 min-h-[300px] max-h-[400px] overflow-y-auto mb-4 pr-2">
                  {chatMessages.map((msg, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                    >
                      <div
                        className={`rounded-2xl px-4 py-3 max-w-[85%] text-sm leading-relaxed whitespace-pre-line ${
                          msg.role === "bot"
                            ? "glass rounded-tl-sm"
                            : "bg-primary text-primary-foreground rounded-tr-sm"
                        }`}
                      >
                        {msg.text}
                      </div>
                    </motion.div>
                  ))}
                  {chatLoading && (
                    <div className="flex gap-3">
                      <div className="glass rounded-2xl rounded-tl-sm px-4 py-3">
                        <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                <div className="flex gap-2 pt-4 border-t border-border/20">
                  <input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleChat()}
                    placeholder="Apna sawaal poochhein..."
                    className="flex-1 bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors"
                  />
                  <Button
                    size="icon"
                    onClick={handleChat}
                    disabled={chatLoading || !chatInput.trim()}
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
