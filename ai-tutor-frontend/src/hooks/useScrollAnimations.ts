"use client"

import { useEffect, useRef } from "react"
import gsap from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"

gsap.registerPlugin(ScrollTrigger)

export function useScrollReveal(ref: React.RefObject<HTMLElement | null>, options?: {
  delay?: number
  duration?: number
  y?: number
  stagger?: number
}) {
  useEffect(() => {
    const el = ref.current
    if (!el) return

    const children = el.children
    const targets = children.length > 0 ? Array.from(children) : [el]

    const ctx = gsap.context(() => {
      gsap.fromTo(
        targets,
        { y: options?.y ?? 60, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: options?.duration ?? 1,
          delay: options?.delay ?? 0,
          stagger: options?.stagger ?? 0.15,
          ease: "power4.out",
          scrollTrigger: {
            trigger: el,
            start: "top 85%",
            end: "bottom 20%",
            toggleActions: "play none none reverse",
          },
        }
      )
    }, el)

    return () => ctx.revert()
  }, [ref, options?.delay, options?.duration, options?.y, options?.stagger])
}

export function useParallax(ref: React.RefObject<HTMLElement | null>, speed: number = 0.5) {
  useEffect(() => {
    const el = ref.current
    if (!el) return

    const ctx = gsap.context(() => {
      gsap.to(el, {
        y: () => -(el.offsetHeight * speed),
        ease: "none",
        scrollTrigger: {
          trigger: el,
          start: "top bottom",
          end: "bottom top",
          scrub: true,
        },
      })
    }, el)

    return () => ctx.revert()
  }, [ref, speed])
}
