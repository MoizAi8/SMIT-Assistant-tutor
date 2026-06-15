"use client"

import { useRef, useMemo, useEffect, useState } from "react"
import { motion } from "framer-motion"
import { Canvas, useFrame, useThree } from "@react-three/fiber"
import { Float, MeshDistortMaterial } from "@react-three/drei"
import * as THREE from "three"
import { Button } from "@/components/ui/button"
import { useTheme } from "@/hooks/useTheme"
import { useScrollReveal } from "@/hooks/useScrollAnimations"
import Link from "next/link"

function Scene({ mouse }: { mouse: THREE.Vector2 }) {
  const { viewport } = useThree()

  const torusRef = useRef<THREE.Mesh>(null)
  const sphereRef = useRef<THREE.Mesh>(null)
  const knotRef = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    const t = state.clock.elapsedTime

    if (torusRef.current) {
      torusRef.current.rotation.x = t * 0.15
      torusRef.current.rotation.y = t * 0.2
      torusRef.current.position.x = mouse.x * 0.5 + Math.sin(t * 0.3) * 0.5
      torusRef.current.position.y = mouse.y * 0.5 + Math.cos(t * 0.4) * 0.3
    }
    if (sphereRef.current) {
      sphereRef.current.rotation.x = t * 0.08
      sphereRef.current.rotation.y = t * 0.12
      sphereRef.current.position.x = mouse.x * 0.3 - 2
      sphereRef.current.position.y = mouse.y * 0.3 + Math.sin(t * 0.2 + 1) * 0.4
    }
    if (knotRef.current) {
      knotRef.current.rotation.x = t * 0.1
      knotRef.current.rotation.y = t * 0.15
      knotRef.current.position.x = mouse.x * 0.4 + 2
      knotRef.current.position.y = mouse.y * 0.4 + Math.cos(t * 0.25 + 2) * 0.5
    }
  })

  return (
    <>
      <ambientLight intensity={0.3} />
      <directionalLight position={[5, 5, 5]} intensity={0.8} />
      <directionalLight position={[-5, -5, -5]} intensity={0.4} />
      <pointLight position={[0, 0, 5]} intensity={0.5} color="#667eea" />

      <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.5}>
        <mesh ref={torusRef} scale={1.2}>
          <torusKnotGeometry args={[1, 0.3, 128, 16]} />
          <MeshDistortMaterial
            color="#667eea"
            emissive="#667eea"
            emissiveIntensity={0.15}
            roughness={0.2}
            metalness={0.8}
            distort={0.15}
            speed={2}
          />
        </mesh>
      </Float>

      <Float speed={0.8} rotationIntensity={0.1} floatIntensity={0.3}>
        <mesh ref={sphereRef} scale={0.6}>
          <icosahedronGeometry args={[1, 1]} />
          <MeshDistortMaterial
            color="#764ba2"
            emissive="#764ba2"
            emissiveIntensity={0.1}
            roughness={0.3}
            metalness={0.6}
            distort={0.1}
            speed={1.5}
          />
        </mesh>
      </Float>

      <Float speed={1.2} rotationIntensity={0.15} floatIntensity={0.4}>
        <mesh ref={knotRef} scale={0.8}>
          <torusGeometry args={[0.8, 0.25, 32, 64]} />
          <MeshDistortMaterial
            color="#4facfe"
            emissive="#4facfe"
            emissiveIntensity={0.1}
            roughness={0.2}
            metalness={0.7}
            distort={0.12}
            speed={1.8}
          />
        </mesh>
      </Float>
    </>
  )
}

export default function Hero3D() {
  const sectionRef = useRef<HTMLElement>(null)
  const mouse = useMemo(() => new THREE.Vector2(0, 0), [])
  const [isReady, setIsReady] = useState(false)
  const { theme } = useTheme()

  useScrollReveal(sectionRef as React.RefObject<HTMLElement | null>, {
    delay: 0,
    y: 0,
  })

  useEffect(() => {
    const handleMouse = (e: MouseEvent) => {
      mouse.x = (e.clientX / window.innerWidth) * 2 - 1
      mouse.y = -(e.clientY / window.innerHeight) * 2 + 1
    }
    window.addEventListener("mousemove", handleMouse)
    setTimeout(() => setIsReady(true), 100)
    return () => window.removeEventListener("mousemove", handleMouse)
  }, [mouse])

  return (
    <section
      ref={sectionRef}
      id="hero"
      className="relative min-h-screen flex items-center overflow-hidden"
    >
      <div className="absolute inset-0 z-0">
        {isReady && (
          <Canvas
            camera={{ position: [0, 0, 6], fov: 50 }}
            dpr={[1, 2]}
            gl={{ antialias: true, alpha: true }}
            style={{ background: "transparent" }}
          >
            <Scene mouse={mouse} />
          </Canvas>
        )}
      </div>

      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/40 to-background z-[1]" />

      <div className="relative z-10 max-width w-full px-6 pt-20">
        <div className="max-w-3xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium border border-primary/20 bg-primary/5 text-primary mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-glow" />
              AI-Powered Code Grading
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-display font-bold leading-[0.95] tracking-tight"
          >
            Teach Smarter
            <br />
            <span className="text-gradient">Grade Better</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="mt-6 text-lg md:text-xl text-muted-foreground max-w-xl leading-relaxed"
          >
            An AI teaching assistant that reviews code, grades by rubric, 
            and gives beginner-friendly feedback in{" "}
            <span className="text-foreground font-medium">simple English + Roman Urdu</span>.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.7 }}
            className="mt-10 flex flex-wrap gap-4"
          >
            <Link href="/grade">
              <Button size="xl" className="relative overflow-hidden group">
                <span className="relative z-10">Try It Free</span>
                <div className="absolute inset-0 bg-gradient-to-r from-primary to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              </Button>
            </Link>
            <a href="#features">
              <Button
                size="xl"
                variant="outline"
                className="border-border hover:border-primary/50"
              >
                Explore Features
              </Button>
            </a>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1, delay: 1 }}
            className="mt-16 flex items-center gap-8 text-sm text-muted-foreground"
          >
            {["Rubric-Based", "Roman Urdu", "Instant Feedback", "Chat Support"].map(
              (item) => (
                <span key={item} className="flex items-center gap-2">
                  <span className="w-1 h-1 rounded-full bg-primary" />
                  {item}
                </span>
              )
            )}
          </motion.div>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10"
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="w-6 h-10 rounded-full border border-border flex items-start justify-center p-2"
        >
          <div className="w-1 h-2 rounded-full bg-muted-foreground" />
        </motion.div>
      </motion.div>
    </section>
  )
}
