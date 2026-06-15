"use client"

import { useEffect, useRef } from "react"
import { useTheme } from "@/hooks/useTheme"

export default function Background() {
  const { theme } = useTheme()
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    let animationId: number
    let particles: Particle[] = []

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener("resize", resize)

    class Particle {
      x: number
      y: number
      size: number
      speedX: number
      speedY: number
      opacity: number
      life: number
      maxLife: number

      constructor() {
        this.x = Math.random() * canvas!.width
        this.y = Math.random() * canvas!.height
        this.size = Math.random() * 2 + 0.5
        this.speedX = (Math.random() - 0.5) * 0.3
        this.speedY = (Math.random() - 0.5) * 0.3
        this.opacity = Math.random() * 0.5 + 0.1
        this.life = 0
        this.maxLife = Math.random() * 300 + 200
      }

      update() {
        this.x += this.speedX
        this.y += this.speedY
        this.life++

        if (this.x < 0) this.x = canvas!.width
        if (this.x > canvas!.width) this.x = 0
        if (this.y < 0) this.y = canvas!.height
        if (this.y > canvas!.height) this.y = 0

        if (this.life > this.maxLife) {
          this.x = Math.random() * canvas!.width
          this.y = Math.random() * canvas!.height
          this.life = 0
          this.opacity = Math.random() * 0.5 + 0.1
        }
      }

      draw() {
        if (!ctx) return
        const hue = theme === "dark" ? 252 : 252
        ctx.beginPath()
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
        ctx.fillStyle = `hsla(${hue}, 80%, 65%, ${this.opacity})`
        ctx.fill()
      }
    }

    const count = Math.min(80, Math.floor((canvas.width * canvas.height) / 15000))
    particles = Array.from({ length: count }, () => new Particle())

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      for (const p of particles) {
        p.update()
        p.draw()
      }

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 120) {
            ctx.beginPath()
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.strokeStyle = `hsla(252, 80%, 65%, ${0.06 * (1 - dist / 120)})`
            ctx.lineWidth = 0.5
            ctx.stroke()
          }
        }
      }

      animationId = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener("resize", resize)
    }
  }, [theme])

  return (
    <>
      <canvas
        ref={canvasRef}
        className="fixed inset-0 z-0 pointer-events-none"
      />
      <div
        className="fixed inset-0 z-0 pointer-events-none"
        style={{
          background:
            theme === "dark"
              ? "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(102, 126, 234, 0.08), transparent), radial-gradient(ellipse 60% 40% at 80% 80%, rgba(118, 75, 162, 0.06), transparent)"
              : "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(102, 126, 234, 0.06), transparent), radial-gradient(ellipse 60% 40% at 80% 80%, rgba(118, 75, 162, 0.04), transparent)",
        }}
      />
    </>
  )
}
