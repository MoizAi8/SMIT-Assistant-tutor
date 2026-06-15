const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface User {
  id: string
  username: string
  role: "admin" | "teacher" | "student"
  display_name: string
  created_at: string
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null
  try {
    return localStorage.getItem("smit_token")
  } catch {
    return null
  }
}

export function setToken(token: string) {
  localStorage.setItem("smit_token", token)
}

export function clearToken() {
  localStorage.removeItem("smit_token")
  localStorage.removeItem("smit_user")
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null
  try {
    const raw = localStorage.getItem("smit_user")
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function storeUser(user: User) {
  localStorage.setItem("smit_user", JSON.stringify(user))
}

export async function login(username: string, password: string): Promise<{ token: string; user: User }> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }))
    throw new Error(err.detail || "Login failed")
  }
  const data = await res.json()
  setToken(data.token)
  storeUser(data.user)
  return data
}

export async function register(
  username: string,
  password: string,
  role: string = "student",
  display_name: string = ""
): Promise<{ token: string; user: User }> {
  const token = getToken()
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ username, password, role, display_name }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Registration failed" }))
    throw new Error(err.detail || "Registration failed")
  }
  const data = await res.json()
  return data
}

export async function getProfile(): Promise<User> {
  const token = getToken()
  if (!token) throw new Error("Not authenticated")
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    clearToken()
    throw new Error("Session expired")
  }
  return res.json()
}

export function authHeaders(): Record<string, string> {
  const token = getToken()
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

export function requireAuth(): string {
  const token = getToken()
  if (!token) {
    if (typeof window !== "undefined") {
      window.location.href = "/login"
    }
    throw new Error("Not authenticated")
  }
  return token
}
