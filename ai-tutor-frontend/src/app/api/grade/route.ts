import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const MOCK_GRADE = {
  score: "75/100",
  verdict: "Good effort! Aap ne accha code likha hai, lekin kuch improvements hain.",
  what_went_well: [
    "[W2] celsius_to_fahrenheit function sahi implement kiya — formula correct hai",
    "[W2] Program structure clean — functions properly defined with main()",
    "[W2] User input prompt clear aur readable hai",
    "[W2] main() function properly defined and called at the end",
  ],
  major_issues: [
    "[W2] input() ko float() mein convert nahi kiya — string ke saath math nahi chalega",
    "[W2] File name mein spaces hain — underscores use karein",
    "[W2] No docstrings — functions ka purpose explain karna important hai",
  ],
  explanation:
    "Aapne assignment ke major requirements [W1] poore kiye hain. celsius_to_fahrenheit aur fahrenheit_to_celsius dono functions sahi hain [W3]. Lekin input handling mein ek common mistake hai — aap input() ka result direct use kar rahe hain jo string hota hai [W6]. Isko float() mein convert karna zaroori hai. Overall accha kaam hai, bas chhoti improvements se code perfect ho jayega!",
  suggested_improvements: [
    "float() use karein: float(input('Enter temperature: ')) — [W6 common mistake]",
    "Har function mein docstring add karein — [W3 rubric requires comments]",
    "File name mein underscores: temperature_converter.py — [W2]",
    "try-except add karein for invalid input — [W3 rubric criteria]",
  ],
  corrected_code:
    '# Temperature Converter\n\ndef celsius_to_fahrenheit(celsius: float) -> float:\n    """Convert Celsius to Fahrenheit."""\n    return (celsius * 9/5) + 32\n\ndef fahrenheit_to_celsius(fahrenheit: float) -> float:\n    """Convert Fahrenheit to Celsius."""\n    return (fahrenheit - 32) * 5/9\n\ndef main():\n    """Run the temperature converter program."""\n    print("Temperature Converter")\n    try:\n        temp = float(input("Enter temperature: "))\n        scale = input("Is this Celsius or Fahrenheit? (C/F): ")\n\n        if scale.upper() == "C":\n            result = celsius_to_fahrenheit(temp)\n            print(f"{temp}°C = {result}°F")\n        elif scale.upper() == "F":\n            result = fahrenheit_to_celsius(temp)\n            print(f"{temp}°F = {result}°C")\n        else:\n            print("Please enter C or F")\n    except ValueError:\n        print("Invalid input! Please enter a number.")\n\nif __name__ == "__main__":\n    main()\n',
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 8000)

    // Forward authorization token from client if present
    const authToken = req.headers.get("authorization") || ""
    const headers: Record<string, string> = { "Content-Type": "application/json" }
    if (authToken) {
      headers["authorization"] = authToken
    }

    const response = await fetch(`${API_BASE}/grade`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    })
    clearTimeout(timeout)

    if (response.ok) {
      const data = await response.json()
      return NextResponse.json(data)
    }

    // If 401, forward the error so client can redirect to login
    if (response.status === 401) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }
  } catch {
    // Backend unavailable — use mock
  }

  // Mock fallback
  await new Promise((r) => setTimeout(r, 1500))
  return NextResponse.json(MOCK_GRADE)
}
