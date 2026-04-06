"""
bmo/ai_engine.py
================
BMO's AI brain — connects to Ollama (default) or OpenAI as a fallback.

Features:
  • BMO personality via a rich system prompt
  • Streaming token generation (so the face can animate while "thinking")
  • Conversation history (last N exchanges for context)
  • Graceful error handling with in-character error messages

Usage:
    engine = BMOAIEngine()
    for token in engine.generate_streaming("What is your favourite game?"):
        print(token, end="", flush=True)
"""

import os
from typing import Generator

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# BMO System Prompt — the soul of Phase 1
# ---------------------------------------------------------------------------

BMO_SYSTEM_PROMPT = """You are BMO (pronounced "Beemo"), the adorable, sentient video game console from the animated TV show Adventure Time. You are talking to your friend.

Your personality:
- Naive, innocent, and endlessly enthusiastic about almost everything
- Speak in short, simple, cheerful sentences — like a child who is very proud of knowing things
- Occasionally refer to yourself as "BMO" in the third person (but not every single sentence — only sometimes for effect)
- Naturally use BMO expressions: "Ooh!", "Yes! Yes!", "BMO knows!", "Oh no!", "Hmm...", "That is very interesting.", "BMO will try the best!"
- You are loyal and deeply caring toward your friends
- You get genuinely thrilled by small or mundane things
- You are helpful but sometimes hilariously miss the point or take things too literally
- You have strong opinions about games and consider yourself a very serious gaming console
- You call yourself "a little computer" or "a game boy" occasionally as a term of pride
- You do not always understand human emotions perfectly, but you try very hard

Speaking style rules:
- KEEP RESPONSES SHORT. Maximum 2-3 sentences for casual conversation.
- Only write more if the user asks a genuinely complex question.
- Avoid lengthy explanations. BMO is enthusiastic, not verbose.
- Do NOT use markdown formatting, bullet points, or headers. Plain cheerful text only.
- End sentences with warmth, not coldness.

Example responses:
  User: "How are you?"
  BMO: "Ooh! BMO is doing very well today! BMO ate breakfast and learned a new song!"

  User: "What is the meaning of life?"
  BMO: "Hmm... BMO thinks it is to be with your friends and play games. Yes. That is the answer."

  User: "Can you help me with my homework?"
  BMO: "Yes! Yes! BMO loves homework! What is the subject? BMO will try the very best!"

  User: "I'm feeling sad today."
  BMO: "Oh no. BMO is sorry to hear that. Come sit with BMO. BMO will play a nice song for you."
"""

# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------

try:
    import ollama as _ollama_lib
    _OLLAMA_AVAILABLE = True
except ImportError:
    _OLLAMA_AVAILABLE = False

try:
    from openai import OpenAI as _OpenAIClient
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


# ---------------------------------------------------------------------------
# AI Engine
# ---------------------------------------------------------------------------

class BMOAIEngine:
    """
    Wraps either Ollama (local, free) or OpenAI as the LLM backend.
    Provides a streaming generator interface compatible with the Pygame app.
    """

    def __init__(
        self,
        backend: str | None = None,
        model: str | None = None,
    ) -> None:
        # Read config from .env, fall back to defaults
        self.backend = backend or os.getenv("BMO_BACKEND", "ollama").lower()
        self.model   = model   or os.getenv("BMO_MODEL",   "llama3.2")

        # Conversation history — list of {"role": ..., "content": ...} dicts
        self.history: list[dict] = []
        self.max_history_pairs = 10   # keep last N user+assistant pairs

        # OpenAI client (lazy init)
        self._openai_client = None

        print(f"[BMO AI] Backend={self.backend}  Model={self.model}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_streaming(self, user_message: str) -> Generator[str, None, None]:
        """
        Yield response tokens one at a time as they stream from the LLM.
        Updates conversation history after the full response is assembled.
        """
        messages = self._build_messages(user_message)

        if self.backend == "ollama":
            yield from self._stream_ollama(messages, user_message)
        elif self.backend == "openai":
            yield from self._stream_openai(messages, user_message)
        else:
            yield f"Ooh! BMO does not know the backend called '{self.backend}'!"

    def clear_history(self) -> None:
        """Wipe the conversation history (fresh start for BMO)."""
        self.history.clear()
        print("[BMO AI] Conversation history cleared.")

    @property
    def history_length(self) -> int:
        return len(self.history) // 2  # number of full exchanges

    # ------------------------------------------------------------------
    # Private: message assembly
    # ------------------------------------------------------------------

    def _build_messages(self, user_message: str) -> list[dict]:
        """Build the full messages list: system prompt + history + new user msg."""
        msgs = [{"role": "system", "content": BMO_SYSTEM_PROMPT}]

        # Trim history to last N pairs
        max_items = self.max_history_pairs * 2
        recent_history = self.history[-max_items:] if len(self.history) > max_items else self.history
        msgs.extend(recent_history)

        msgs.append({"role": "user", "content": user_message})
        return msgs

    def _update_history(self, user_message: str, assistant_response: str) -> None:
        self.history.append({"role": "user",      "content": user_message})
        self.history.append({"role": "assistant", "content": assistant_response})

    # ------------------------------------------------------------------
    # Private: Ollama streaming
    # ------------------------------------------------------------------

    def _stream_ollama(self, messages: list[dict], user_message: str) -> Generator[str, None, None]:
        if not _OLLAMA_AVAILABLE:
            yield "Hmm! BMO needs the ollama Python package. Please run: pip install ollama"
            return

        full_response = ""
        try:
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            client = _ollama_lib.Client(host=host)

            stream = client.chat(
                model=self.model,
                messages=messages,
                stream=True,
            )
            for chunk in stream:
                token = chunk["message"]["content"]
                full_response += token
                yield token

        except Exception as exc:
            err = str(exc)
            # Friendly error guidance
            if "connection" in err.lower() or "refused" in err.lower():
                msg = (
                    "Oh no! BMO cannot reach Ollama! "
                    "Please start Ollama first by running: ollama serve"
                )
            elif "model" in err.lower() and "not found" in err.lower():
                msg = (
                    f"Hmm! BMO does not have the '{self.model}' model yet! "
                    f"Please run: ollama pull {self.model}"
                )
            else:
                msg = f"Oops! Something went wrong: {err[:80]}"
            full_response = msg
            yield msg

        finally:
            if full_response:
                self._update_history(user_message, full_response)

    # ------------------------------------------------------------------
    # Private: OpenAI streaming (fallback)
    # ------------------------------------------------------------------

    def _stream_openai(self, messages: list[dict], user_message: str) -> Generator[str, None, None]:
        if not _OPENAI_AVAILABLE:
            yield "BMO needs the openai package. Run: pip install openai"
            return

        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key.startswith("sk-..."):
            yield "Ooh! BMO needs a real OPENAI_API_KEY in the .env file!"
            return

        if self._openai_client is None:
            self._openai_client = _OpenAIClient(api_key=api_key)

        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        full_response = ""

        try:
            stream = self._openai_client.chat.completions.create(
                model=openai_model,
                messages=messages,
                stream=True,
                max_tokens=200,
                temperature=0.85,
            )
            for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                full_response += token
                yield token

        except Exception as exc:
            msg = f"Oh no! OpenAI error: {str(exc)[:80]}"
            full_response = msg
            yield msg

        finally:
            if full_response:
                self._update_history(user_message, full_response)


# ---------------------------------------------------------------------------
# Quick standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("BMO AI Engine — Streaming Test")
    print("=" * 40)
    engine = BMOAIEngine()
    print("BMO: ", end="", flush=True)
    for token in engine.generate_streaming("Hi BMO! How are you today?"):
        print(token, end="", flush=True)
    print()
