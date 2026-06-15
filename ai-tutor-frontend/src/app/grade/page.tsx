"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { ArrowLeft, Upload, FileCode2, ScrollText, Brain, Loader2, LogOut } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import Link from "next/link"
import { useAuth } from "@/contexts/AuthContext"
import { getToken } from "@/lib/auth"

export default function GradePage() {
  const router = useRouter()
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    assignment_title: "",
    assignment_instructions: "",
    rubric: "",
    total_marks: 100,
    student_code: "",
    file_name: "",
    folder_structure: "",
    expected_output: "",
    sample_output: "",
    previous_feedback: "",
    class_notes: "",
    common_mistakes: "",
    student_name: "",
  })

  const update = (key: string, value: string | number) =>
    setForm((prev) => ({ ...prev, [key]: value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.student_code.trim() || !form.rubric.trim() || !form.assignment_instructions.trim()) {
      alert("Please fill in student code, rubric, and assignment instructions.")
      return
    }
    setLoading(true)
    try {
      const token = getToken()
      const headers: Record<string, string> = { "Content-Type": "application/json" }
      if (token) headers["Authorization"] = `Bearer ${token}`

      const res = await fetch("/api/grade", {
        method: "POST",
        headers,
        body: JSON.stringify(form),
      })
      if (res.status === 401) {
        router.push("/login")
        return
      }
      if (!res.ok) throw new Error("Grading failed")
      const data = await res.json()
      sessionStorage.setItem("lastGrade", JSON.stringify(data))
      router.push("/result")
    } catch (err) {
      alert("Failed to grade. Make sure the backend server is running on port 8000.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen pt-24 pb-16">
      <div className="max-width px-6">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground font-medium">
            Grade a Submission
          </span>
          <h1 className="text-4xl md:text-5xl font-display font-bold mt-3 leading-tight">
            Submit code for{" "}
            <span className="text-gradient">AI review</span>
          </h1>
          <p className="mt-3 text-muted-foreground">
            Fill in the details below and get a rubric-based evaluation with feedback in simple English + Roman Urdu.
          </p>
        </motion.div>

        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left: Main inputs */}
            <div className="lg:col-span-2 space-y-6">
              <Card glass className="p-6">
                <h2 className="flex items-center gap-2 font-semibold mb-4">
                  <FileCode2 className="w-4 h-4 text-primary" /> Assignment & Code
                </h2>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                        Assignment Title
                      </label>
                      <input
                        value={form.assignment_title}
                        onChange={(e) => update("assignment_title", e.target.value)}
                        placeholder="e.g. Temperature Converter"
                        className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                        Student Name
                      </label>
                      <input
                        value={form.student_name}
                        onChange={(e) => update("student_name", e.target.value)}
                        placeholder="e.g. Ali"
                        className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                      Assignment Instructions *
                    </label>
                    <textarea
                      value={form.assignment_instructions}
                      onChange={(e) => update("assignment_instructions", e.target.value)}
                      placeholder="Paste the full assignment description here..."
                      rows={5}
                      className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors resize-none font-mono"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                      Student Code *
                    </label>
                    <textarea
                      value={form.student_code}
                      onChange={(e) => update("student_code", e.target.value)}
                      placeholder="Paste the student's code here..."
                      rows={12}
                      className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors resize-none font-mono"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                        File Name
                      </label>
                      <input
                        value={form.file_name}
                        onChange={(e) => update("file_name", e.target.value)}
                        placeholder="e.g. main.py"
                        className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                        Total Marks
                      </label>
                      <input
                        type="number"
                        value={form.total_marks}
                        onChange={(e) => update("total_marks", parseInt(e.target.value) || 100)}
                        className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                      Folder Structure
                    </label>
                    <textarea
                      value={form.folder_structure}
                      onChange={(e) => update("folder_structure", e.target.value)}
                      placeholder="Describe or paste the folder structure..."
                      rows={3}
                      className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors resize-none font-mono"
                    />
                  </div>
                </div>
              </Card>

              <Card glass className="p-6">
                <h2 className="flex items-center gap-2 font-semibold mb-4">
                  <ScrollText className="w-4 h-4 text-primary" /> Rubric
                </h2>
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                    Rubric / Marking Scheme *
                  </label>
                  <textarea
                    value={form.rubric}
                    onChange={(e) => update("rubric", e.target.value)}
                    placeholder="Paste the rubric with criteria and point values..."
                    rows={8}
                    className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors resize-none font-mono"
                  />
                </div>
              </Card>
            </div>

            {/* Right: Optional inputs */}
            <div className="space-y-6">
              <Card glass className="p-6">
                <h2 className="flex items-center gap-2 font-semibold mb-4">
                  <Brain className="w-4 h-4 text-primary" /> Expected Output
                </h2>
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                      Expected Output
                    </label>
                    <textarea
                      value={form.expected_output}
                      onChange={(e) => update("expected_output", e.target.value)}
                      placeholder="What the output should look like..."
                      rows={4}
                      className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors resize-none font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                      Sample Output
                    </label>
                    <textarea
                      value={form.sample_output}
                      onChange={(e) => update("sample_output", e.target.value)}
                      placeholder="Example of correct output..."
                      rows={4}
                      className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors resize-none font-mono"
                    />
                  </div>
                </div>
              </Card>

              <Card glass className="p-6">
                <h2 className="flex items-center gap-2 font-semibold mb-4">
                  Knowledge Base
                </h2>
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                      Previous Feedback
                    </label>
                    <textarea
                      value={form.previous_feedback}
                      onChange={(e) => update("previous_feedback", e.target.value)}
                      placeholder="Past feedback for this student..."
                      rows={3}
                      className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors resize-none"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                      Class Notes
                    </label>
                    <textarea
                      value={form.class_notes}
                      onChange={(e) => update("class_notes", e.target.value)}
                      placeholder="Relevant class notes..."
                      rows={3}
                      className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors resize-none"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                      Common Mistakes
                    </label>
                    <textarea
                      value={form.common_mistakes}
                      onChange={(e) => update("common_mistakes", e.target.value)}
                      placeholder="Known common mistakes for this assignment..."
                      rows={3}
                      className="w-full bg-transparent border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-colors resize-none"
                    />
                  </div>
                </div>
              </Card>

              <Button
                type="submit"
                size="xl"
                disabled={loading}
                className="w-full group relative overflow-hidden"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Grading...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Upload className="w-4 h-4" />
                    Submit for Grading
                  </span>
                )}
                <div className="absolute inset-0 bg-gradient-to-r from-primary to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
