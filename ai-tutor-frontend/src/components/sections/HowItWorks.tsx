"use client"

import { useRef } from "react"
import { motion } from "framer-motion"
import { FileCode2, ClipboardList, MessageSquareText, GraduationCap } from "lucide-react"
import { useScrollReveal } from "@/hooks/useScrollAnimations"

const steps = [
  {
    number: "01",
    icon: FileCode2,
    title: "Submit Code",
    desc: "Student uploads their code with file name and folder structure.",
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    number: "02",
    icon: ClipboardList,
    title: "Rubric Check",
    desc: "Agent reads the assignment rubric and checks every criterion against visible evidence.",
    gradient: "from-purple-500 to-pink-500",
  },
  {
    number: "03",
    icon: MessageSquareText,
    title: "Get Feedback",
    desc: "Detailed feedback in simple English + Roman Urdu with specific line references.",
    gradient: "from-amber-500 to-orange-500",
  },
  {
    number: "04",
    icon: GraduationCap,
    title: "Learn & Improve",
    desc: "Chat with the AI to clarify doubts and see corrected code with improvements.",
    gradient: "from-green-500 to-emerald-500",
  },
]

export default function HowItWorks() {
  const ref = useRef<HTMLElement>(null)
  useScrollReveal(ref as React.RefObject<HTMLElement | null>, { stagger: 0.15 })

  return (
    <section ref={ref} id="how-it-works" className="section-padding relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-primary/3 to-transparent pointer-events-none" />

      <div className="max-width relative">
        <motion.div className="text-center max-w-2xl mx-auto mb-20">
          <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground font-medium">
            Workflow
          </span>
          <h2 className="text-4xl md:text-5xl font-display font-bold mt-4 leading-tight">
            From submission to{" "}
            <span className="text-gradient-2">mastery</span>
          </h2>
          <p className="mt-4 text-muted-foreground text-lg">
            Four simple steps from code submission to deeper understanding.
          </p>
        </motion.div>

        <div className="relative">
          <div className="hidden lg:block absolute top-24 left-[calc(12.5%+24px)] right-[calc(12.5%+24px)] h-px bg-gradient-to-r from-primary/0 via-primary/20 to-primary/0" />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-6">
            {steps.map((step, i) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ delay: i * 0.15, duration: 0.6 }}
                className="relative text-center lg:text-left"
              >
                <div className="flex flex-col items-center lg:items-start">
                  <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${step.gradient} p-4 mb-6 flex items-center justify-center relative`}>
                    <step.icon className="w-full h-full text-white" />
                    <span className="absolute -top-2 -right-2 w-7 h-7 rounded-full bg-background border border-border flex items-center justify-center text-xs font-bold text-foreground">
                      {step.number}
                    </span>
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed max-w-xs">{step.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
