"use client"

import { useRef, useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { MessageSquare, Code2, Send, Bot } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { useScrollReveal } from "@/hooks/useScrollAnimations"

const demoMessages = [
  { role: "bot", text: "Assalam-o-Alaikum! Main aapki code submission check kar raha hoon..." },
  { role: "bot", text: "Aapne celsius_to_fahrenheit function accha likha hai! ✅" },
  { role: "bot", text: "Lekin input() ko float() mein convert karna bhool gaye. Yeh ek common mistake hai." },
  { role: "bot", text: "Yeh raha corrected code:\n\ndef celsius_to_fahrenheit(c):\n    return (c * 9/5) + 32\n\ntemp = float(input(\"Enter temperature: \"))\nresult = celsius_to_fahrenheit(temp)\nprint(f\"{temp}°C = {result}°F\")" },
]

export default function AgentDemo() {
  const ref = useRef<HTMLElement>(null)
  const [visibleMessages, setVisibleMessages] = useState(0)
  const [userInput, setUserInput] = useState("")
  const [chatStarted, setChatStarted] = useState(false)

  useScrollReveal(ref as React.RefObject<HTMLElement | null>, { stagger: 0.1 })

  useEffect(() => {
    if (visibleMessages < demoMessages.length) {
      const timer = setTimeout(() => setVisibleMessages((p) => p + 1), 1800)
      return () => clearTimeout(timer)
    }
  }, [visibleMessages])

  const handleSend = () => {
    if (!userInput.trim()) return
    setUserInput("")
  }

  return (
    <section ref={ref} id="agent" className="section-padding relative">
      <div className="max-width">
        <motion.div className="text-center max-w-2xl mx-auto mb-16">
          <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground font-medium">
            Live Demo
          </span>
          <h2 className="text-4xl md:text-5xl font-display font-bold mt-4 leading-tight">
            See the agent in{" "}
            <span className="text-gradient">action</span>
          </h2>
          <p className="mt-4 text-muted-foreground text-lg">
            Watch how the AI Teaching Assistant grades code and gives feedback.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
          >
            <Card glass className="p-6 overflow-hidden">
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border/30">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 p-2">
                  <Bot className="w-full h-full text-white" />
                </div>
                <div>
                  <p className="font-semibold text-sm">Teaching Assistant</p>
                  <p className="text-xs text-muted-foreground">Online — reviewing code</p>
                </div>
                <div className="ml-auto flex gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-glow" />
                  <div className="w-2 h-2 rounded-full bg-yellow-500/30" />
                  <div className="w-2 h-2 rounded-full bg-red-500/30" />
                </div>
              </div>

              <div className="space-y-3 min-h-[320px]">
                <AnimatePresence>
                  {demoMessages.slice(0, visibleMessages).map((msg, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10, scale: 0.98 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ duration: 0.4 }}
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
                </AnimatePresence>

                {visibleMessages === 0 && (
                  <div className="flex items-center justify-center h-[280px]">
                    <motion.div
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="flex items-center gap-2 text-muted-foreground text-sm"
                    >
                      <Code2 className="w-4 h-4" />
                      Analyzing submission...
                    </motion.div>
                  </div>
                )}

                {visibleMessages >= demoMessages.length && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="pt-4 border-t border-border/20"
                  >
                    <p className="text-xs text-muted-foreground mb-3">
                      Score: <span className="text-primary font-semibold">75/100</span> &middot; Grade: B
                    </p>
                    <div className="flex gap-2">
                      <input
                        value={userInput}
                        onChange={(e) => setUserInput(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleSend()}
                        placeholder="Ask about your grade..."
                        className="flex-1 bg-transparent border border-border rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-primary/50 transition-colors"
                      />
                      <Button size="icon" variant="ghost" onClick={handleSend}>
                        <Send className="w-4 h-4" />
                      </Button>
                    </div>
                  </motion.div>
                )}
              </div>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="space-y-4"
          >
            <Card glass className="p-6">
              <h3 className="font-semibold mb-2 text-sm uppercase tracking-wider text-muted-foreground">
                Grading Result
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Requirements</span>
                  <span className="text-sm font-medium">22/30</span>
                </div>
                <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: "73%" }}
                    viewport={{ once: true }}
                    className="h-full rounded-full bg-blue-500"
                  />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Correctness</span>
                  <span className="text-sm font-medium">24/30</span>
                </div>
                <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: "80%" }}
                    viewport={{ once: true }}
                    className="h-full rounded-full bg-purple-500"
                  />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Code Quality</span>
                  <span className="text-sm font-medium">16/20</span>
                </div>
                <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: "80%" }}
                    viewport={{ once: true }}
                    className="h-full rounded-full bg-amber-500"
                  />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Output</span>
                  <span className="text-sm font-medium">13/20</span>
                </div>
                <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: "65%" }}
                    viewport={{ once: true }}
                    className="h-full rounded-full bg-green-500"
                  />
                </div>
                <div className="pt-3 border-t border-border/20 flex justify-between">
                  <span className="font-semibold">Total</span>
                  <span className="font-bold text-lg text-gradient">75/100</span>
                </div>
              </div>
            </Card>

            <Card glass className="p-6">
              <h3 className="font-semibold mb-3 text-sm uppercase tracking-wider text-muted-foreground">
                What Went Well
              </h3>
              <ul className="space-y-2">
                {[
                  "celsius_to_fahrenheit function sahi hai",
                  "Program structure clean hai",
                  "User input prompt clear hai",
                  "Main() function properly defined",
                ].map((item, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-start gap-2 text-sm"
                  >
                    <span className="text-green-500 mt-0.5">+</span>
                    {item}
                  </motion.li>
                ))}
              </ul>
            </Card>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
