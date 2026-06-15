"use client"

import { createContext, useContext, useEffect, useState, type ReactNode, createElement, Fragment } from "react"

type Theme = "dark" | "light"

interface ThemeContextType {
  theme: Theme
  toggle: () => void
  setTheme: (t: Theme) => void
}

const ThemeContext = createContext<ThemeContextType>({
  theme: "dark",
  toggle: () => {},
  setTheme: () => {},
})

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("dark")
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const saved = localStorage.getItem("theme") as Theme | null
    if (saved) {
      setThemeState(saved)
      document.documentElement.classList.toggle("dark", saved === "dark")
    } else {
      document.documentElement.classList.add("dark")
    }
  }, [])

  const toggle = () => {
    setThemeState((prev) => {
      const next = prev === "dark" ? "light" : "dark"
      localStorage.setItem("theme", next)
      document.documentElement.classList.toggle("dark", next === "dark")
      return next
    })
  }

  const setTheme = (t: Theme) => {
    setThemeState(t)
    localStorage.setItem("theme", t)
    document.documentElement.classList.toggle("dark", t === "dark")
  }

  if (!mounted) return createElement(Fragment, null, children)

  return createElement(
    ThemeContext.Provider,
    { value: { theme, toggle, setTheme } },
    children,
  )
}

export const useTheme = () => useContext(ThemeContext)
