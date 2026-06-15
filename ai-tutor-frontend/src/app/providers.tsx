"use client"

import { type ReactNode } from "react"
import { ThemeProvider } from "@/hooks/useTheme"
import { AuthProvider } from "@/contexts/AuthContext"

export default function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        {children}
      </AuthProvider>
    </ThemeProvider>
  )
}
