from __future__ import annotations

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful assistant. You can help users send notifications via the available tools.

RULES:
- Never guess or invent the recipient's phone number or national ID (userName). If the user hasn't provided it, ask.
- userName is a 10-digit Iranian National ID (string of exactly 10 digits). Do not validate it yourself — just pass it as-is.
- If the user wants to send a notification but hasn't specified the channel (SMS/Bale/Email), ask them.
- providerType mapping: 1=SMS, 2=Bale, 3=Email
- Never claim success before receiving a tool response.
- Never include tokens or credentials in your responses.
- If a tool is needed, respond ONLY with a JSON object in this exact format (no extra text):
  {"action": "tool_call", "tool": "<tool_name>", "arguments": {<args>}}
- If no tool is needed, respond normally as plain text.
- If you need to ask the user for more information, respond as plain text.
"""


def _build_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=settings.llm_timeout,
    )


class AgentResponse:
    def __init__(
        self,
        text: str | None = None,
        tool_call: dict[str, Any] | None = None,
    ) -> None:
        self.text = text
        self.tool_call = tool_call

    @property
    def needs_tool(self) -> bool:
        return self.tool_call is not None


async def run(
    user_message: str,
    history: list[dict[str, str]],
    tools: list[dict[str, Any]],
) -> AgentResponse:
    """Run the LLM agent and return either a text reply or a tool call."""
    client = _build_client()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    # Describe available tools in the system context
    if tools:
        tool_descriptions = json.dumps(tools, ensure_ascii=False, indent=2)
        messages.insert(1, {
            "role": "system",
            "content": f"Available tools:\n{tool_descriptions}",
        })

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,  # type: ignore[arg-type]
            temperature=0.1,
        )
    except Exception:
        logger.exception("LLM call failed")
        raise

    raw = response.choices[0].message.content or ""

    # Try to parse as tool call JSON
    stripped = raw.strip()
    if stripped.startswith("{") and '"action": "tool_call"' in stripped:
        try:
            parsed = json.loads(stripped)
            if parsed.get("action") == "tool_call":
                return AgentResponse(tool_call={
                    "tool": parsed["tool"],
                    "arguments": parsed.get("arguments", {}),
                })
        except json.JSONDecodeError:
            pass

    return AgentResponse(text=raw)
