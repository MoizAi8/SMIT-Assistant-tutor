import type { Metadata } from "next"
import { Inter, JetBrains_Mono } from "next/font/google"
import Providers from "./providers"
import SmoothScroll from "@/components/layout/SmoothScroll"
import Navbar from "@/components/layout/Navbar"
import Background from "@/components/effects/Background"
import "./globals.css"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
})

export const metadata: Metadata = {
  title: "SMIT ASSISTANT TUTOR — Smart Code Grading Assistant",
  description:
    "An AI teaching assistant that reviews code submissions, grades by rubric, and gives beginner-friendly feedback in simple English + Roman Urdu.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('theme');
                  if (theme === 'light') {
                    document.documentElement.classList.remove('dark');
                  } else {
                    document.documentElement.classList.add('dark');
                  }
                } catch(e) {}
              })();
            `,
          }}
        />
      </head>
      <body className={`${inter.variable} ${jetbrainsMono.variable}`}>
        <Providers>
          <SmoothScroll>
            <Background />
            <Navbar />
            <main className="relative z-10">{children}</main>
          </SmoothScroll>
        </Providers>
      </body>
    </html>
  )
}
