"use client"

import { useRef } from "react"
import { motion } from "framer-motion"
import { Brain, MessageSquareText, ScrollText, Sparkles, Shield, Zap } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { useScrollReveal } from "@/hooks/useScrollAnimations"

const features = [
  {
    icon: Brain,
    title: "AI-Powered Analysis",
    desc: "Deep code review that checks syntax, logic, structure, naming, imports, and completeness against your rubric.",
    gradient: "from-blue-500 to-purple-500",
  },
  {
    icon: MessageSquareText,
    title: "Roman Urdu Support",
    desc: "Concepts explained in simple English + Roman Urdu so every student truly understands.",
    gradient: "from-purple-500 to-pink-500",
  },
  {
    icon: ScrollText,
    title: "Rubric-Only Grading",
    desc: "Never invents marks. Every score is backed by visible evidence from the rubric and code.",
    gradient: "from-amber-500 to-orange-500",
  },
  {
    icon: Sparkles,
    title: "Corrected Code",
    desc: "Automatically generates corrected code with fixes applied, so students see exactly what to change.",
    gradient: "from-green-500 to-emerald-500",
  },
  {
    icon: Shield,
    title: "Guardrails Built-In",
    desc: "Input and output guardrails prevent hallucinated marks and ensure fair, consistent grading.",
    gradient: "from-rose-500 to-red-500",
  },
  {
    icon: Zap,
    title: "Interactive Chatbot",
    desc: "Post-grading chat sessions where students ask questions and get friendly explanations.",
    gradient: "from-cyan-500 to-blue-500",
  },
]

export default function Features() {
  const ref = useRef<HTMLElement>(null)
  useScrollReveal(ref as React.RefObject<HTMLElement | null>, { stagger: 0.1 })

  return (
    <section ref={ref} id="features" className="section-padding relative">
      <div className="max-width">
        <motion.div className="text-center max-w-2xl mx-auto mb-20">
          <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground font-medium">
            Features
          </span>
          <h2 className="text-4xl md:text-5xl font-display font-bold mt-4 leading-tight">
            Everything you need to{" "}
            <span className="text-gradient">grade fairly</span>
          </h2>
          <p className="mt-4 text-muted-foreground text-lg">
            From rubric analysis to interactive chat — one platform for better teaching.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ delay: i * 0.1, duration: 0.6 }}
            >
              <Card glass className="group relative overflow-hidden p-6 h-full hover:shadow-xl transition-shadow duration-500">
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br from-primary/5 to-transparent" />
                <div className="relative z-10">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.gradient} p-2.5 mb-5`}>
                    <f.icon className="w-full h-full text-white" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
                </div>
                <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
