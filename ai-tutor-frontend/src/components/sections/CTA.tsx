"use client"

import { useRef } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { ArrowRight, Sparkles } from "lucide-react"
import { useScrollReveal } from "@/hooks/useScrollAnimations"
import Link from "next/link"

export default function CTA() {
  const ref = useRef<HTMLElement>(null)
  useScrollReveal(ref as React.RefObject<HTMLElement | null>)

  return (
    <section ref={ref} className="section-padding relative">
      <div className="max-width">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="relative overflow-hidden rounded-3xl p-12 md:p-20 text-center"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-purple-600/5 to-transparent" />
          <div className="absolute inset-0 bg-noise opacity-20" />

          <div className="relative z-10 max-w-2xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium border border-primary/20 bg-primary/5 text-primary mb-6"
            >
              <Sparkles className="w-3 h-3" />
              Start Grading Smarter
            </motion.div>

            <h2 className="text-4xl md:text-5xl font-display font-bold leading-tight">
              Ready to transform how you{" "}
              <span className="text-gradient">teach code</span>?
            </h2>

            <p className="mt-6 text-lg text-muted-foreground max-w-lg mx-auto">
              Join instructors who use AI to give fair, detailed, and encouraging feedback — 
              in the language their students understand best.
            </p>

            <div className="mt-10 flex flex-wrap justify-center gap-4">
              <Link href="/grade">
                <Button size="xl" className="group">
                  Get Started Free
                  <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
              <a href="#features">
                <Button size="xl" variant="outline">
                  Learn More
                </Button>
              </a>
            </div>

            <p className="mt-6 text-xs text-muted-foreground">
              No credit card required &middot; Free tier included &middot; Set up in 2 minutes
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
