import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const MOCK_RESPONSES = [
  "Bilkul! Yeh issue aapke code mein variable naming ka hai. Python mein snake_case use karte hain.",
  "Aapne poochha ke score 75/100 kyun hai? Chaliye batata hoon...",
  "Bohot acha sawaal hai! Aap try-except ka use karke error handle kar sakte hain.",
  "Haan, docstrings add karna acchi practice hai.",
  "Mujhe iska pata nahi, lekin main aapko bata sakta hoon ke kaise seekhein.",
]

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 10000)

    // Forward authorization token from client if present
    const authToken = req.headers.get("authorization") || ""
    const headers: Record<string, string> = { "Content-Type": "application/json" }
    if (authToken) {
      headers["authorization"] = authToken
    }

    const payload: Record<string, unknown> = {
      session_id: body.session_id,
      message: body.message,
    }
    if (body.grade_context) {
      payload.grade_context = body.grade_context
    }

    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
      signal: controller.signal,
    })
    clearTimeout(timeout)

    if (response.ok) {
      const data = await response.json()
      return NextResponse.json(data)
    }

    if (response.status === 401) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }
  } catch {
    // Backend unavailable — use mock
  }

  // Mock fallback
  await new Promise((r) => setTimeout(r, 800 + Math.random() * 1200))
  const idx = Math.floor(Math.random() * MOCK_RESPONSES.length)
  return NextResponse.json({
    session_id: `mock_${Date.now()}`,
    response: MOCK_RESPONSES[idx],
  })
}
