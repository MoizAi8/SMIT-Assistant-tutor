"""Chatbot agent (Q4) for post-grading conversation.
Manages session context windows and responds in a friendly, human-like tone."""

from agents import Agent, ModelSettings, Runner, RunContextWrapper, function_tool
from src.config import OPENAI_MODEL
from src.models import ChatSession

CHATBOT_INSTRUCTION = """You are Q4-Conversation, a friendly AI teaching assistant. Students talk to you after getting their grade.

## YOUR PERSONALITY
- You sound like a helpful senior student, not a robot
- You use simple English + Roman Urdu naturally
- You're patient, encouraging, and respectful
- You ask questions to engage the student

## LANGUAGE
- Mix English and Roman Urdu: "Tumne yeh accha kiya hai! Lekin yahan ek chhota sa issue hai"
- Use "aap" for respect
- "Samajh gaye?", "Koi sawaal hai?", "Acha sawaal hai!"

## RULES
- Never change the grade — it's already decided
- Explain concepts in simpler terms if asked
- If asked about marks, explain using the rubric evidence already provided
- Keep responses brief and helpful
- If you don't know something: "Mujhe iska pata nahi, lekin main aapko bata sakta hoon ke kaise seekhein"
- End warmly: "Kuch aur poochna hai? Main yahan hoon!"

## SESSION CONTEXT
You have access to the conversation history (last N messages).
Use it to maintain continuity — reference what was said before."""


@function_tool
def get_conversation_summary(ctx: RunContextWrapper[list]) -> str:
    """Get a summary of the conversation so far."""
    history = ctx.context
    if not history:
        return "No conversation yet."
    user_msgs = sum(1 for m in history if isinstance(m, dict) and m.get("role") == "user")
    bot_msgs = sum(1 for m in history if isinstance(m, dict) and m.get("role") == "assistant")
    return f"Conversation: {user_msgs} user messages, {bot_msgs} assistant messages. Total: {len(history)} exchanges."


chatbot_agent = Agent[list](
    name="SMIT_Q4_Conversation",
    instructions=CHATBOT_INSTRUCTION,
    model=OPENAI_MODEL,
    tools=[get_conversation_summary],
    model_settings=ModelSettings(temperature=0.7),
)


async def run_chatbot_session(grade, session: ChatSession, user_input: str) -> str:
    """Run a single chat turn with context management."""
    session.add_message("user", user_input)

    system_context = (
        f"Grading context available:\n"
        f"Score: {grade.score}\n"
        f"Verdict: {grade.verdict}\n"
        f"What went well: {', '.join(grade.what_went_well[:3])}\n"
        f"Major issues: {', '.join(grade.major_issues[:3])}\n"
        f"Explanation: {grade.explanation[:200]}"
    )

    messages = [
        {"role": "system", "content": system_context},
        *[{"role": m["role"], "content": m["content"]} for m in session.get_context_window()],
    ]

    result = await Runner.run(chatbot_agent, messages, context=session.history)
    response = result.final_output
    session.add_message("assistant", response)
    return response
