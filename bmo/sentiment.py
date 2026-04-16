"""
bmo/sentiment.py
================
Maps AI response text → expression name using VADER sentiment analysis
plus keyword/pattern overrides for BMO-specific logic.

Usage:
    from bmo.sentiment import SentimentAnalyzer
    sa = SentimentAnalyzer()
    expression = sa.analyze("Ooh! That is so exciting!!!")  # → "excited"
"""

import re

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _vader_available = True
except ImportError:
    _vader_available = False
    print("[BMO] Warning: vaderSentiment not installed. Falling back to keyword-only mode.")


# ---------------------------------------------------------------------------
# Keyword / pattern overrides (checked BEFORE VADER scores)
# These catch BMO-specific language patterns reliably.
# ---------------------------------------------------------------------------

# Maps regex pattern → expression name. First match wins.
KEYWORD_RULES: list[tuple[str, str]] = [
    # Thinking indicators
    (r"\bhmm+\b|\blet me think\b|\bthinking\b|\bwonder\b|\bhm\b", "thinking"),

    # Sleeping / tired
    (r"\bzzz\b|\bsleeping\b|\bsleep\b|\btired\b", "sleeping"),

    # New exact matches/emoticons (escape properly)
    (r"(:D|\bxd\b|\bwide grin\b)", "wide_smile"),
    (r"(D:|shocked|gasp|horrified)", "shocked"),
    (r"(-_-|\bflat\b|\bbored\b|\bwhatever\b|\bmeh\b)", "flat"),
    (r"(\bdizzy\b|\bconfused\b|\bspinning\b|\bwoozy\b)", "dizzy"),
    (r"(\blove\b|<3|\bheart\b|\badores?\b)", "love"),
    (r"(\bcrying\b|\bcry\b|\bsobbing\b|\btears\b)", "crying"),

    # Surprised / shocked (fallback from D:)
    (r"wh?oa+!|\bomg\b|\boh my\b|\bno way\b|\bwhat!\b", "surprised"),

    # Excited (very positive, many exclamation marks, or explicit words)
    (r"\byes! yes!\b|\boh! oh!\b|\byes+!\b|\bwoo+\b|\bamazing!\b|\bincredible!\b", "excited"),

    # Sad
    (r"\b(oh no|sad|sorry|terrible|awful|unfortunately|i am sorry)\b", "sad"),
]

_COMPILED_RULES = [(re.compile(pat, re.IGNORECASE), expr) for pat, expr in KEYWORD_RULES]


def _count_exclamations(text: str) -> int:
    return text.count("!")


def _has_many_exclamations(text: str, threshold: int = 2) -> bool:
    return _count_exclamations(text) >= threshold


class SentimentAnalyzer:
    """Lightweight sentiment → expression mapper."""

    def __init__(self) -> None:
        if _vader_available:
            self._vader = SentimentIntensityAnalyzer()
        else:
            self._vader = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, text: str) -> str:
        """
        Return the most appropriate BMO expression name for the given text.

        Priority order:
          1. Keyword / pattern overrides
          2. VADER compound score mapping
          3. Exclamation count boost
          4. Fallback → "neutral"
        """
        if not text or not text.strip():
            return "neutral"

        # 1. Keyword overrides
        for pattern, expression in _COMPILED_RULES:
            if pattern.search(text):
                # Still allow exclamation boost to upgrade sad/thinking → excited
                if expression not in ("thinking", "sleeping") and _has_many_exclamations(text, 3):
                    return "excited"
                return expression

        # 2. VADER scoring
        if self._vader:
            scores = self._vader.polarity_scores(text)
            compound = scores["compound"]
            expression = self._compound_to_expression(compound, text)
        else:
            # Fallback: purely keyword/exclamation based
            expression = "neutral"

        # 3. Exclamation count boost (3+ !! upgrades positive → excited)
        if expression in ("happy", "neutral") and _has_many_exclamations(text, 3):
            expression = "excited"

        return expression

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compound_to_expression(compound: float, text: str) -> str:
        """
        Map a VADER compound score [-1, 1] to an expression name.

        Thresholds tuned for BMO's short, cheerful responses:
          ≥ 0.65  → excited  (very positive)
          ≥ 0.20  → happy
          ≥ -0.15 → neutral  (or talking — caller decides)
          ≥ -0.50 → sad
          <  -0.50 → sad
        """
        if compound >= 0.65:
            return "excited"
        elif compound >= 0.20:
            return "happy"
        elif compound >= -0.15:
            return "neutral"
        else:
            return "sad"

    def analyze_for_debug(self, text: str) -> dict:
        """Return detailed analysis info for debugging."""
        result = {
            "text": text[:80],
            "expression": self.analyze(text),
            "exclamations": _count_exclamations(text),
        }
        if self._vader:
            result["vader_scores"] = self._vader.polarity_scores(text)
        # Check keyword matches
        for pattern, expr in _COMPILED_RULES:
            if pattern.search(text):
                result["keyword_match"] = expr
                break
        return result


# ---------------------------------------------------------------------------
# Quick standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sa = SentimentAnalyzer()
    test_cases = [
        ("Ooh! BMO knows! That is so amazing!!!", "excited"),
        ("I am happy to help you today!", "happy"),
        ("Hmm, let me think about that...", "thinking"),
        ("Oh no, that is very sad news.", "sad"),
        ("Yes! Yes! Yes! BMO loves this!!!", "excited"),
        ("Whoa! No way!", "surprised"),
        ("BMO understands. Okay.", "neutral"),
        ("That is terrible. BMO is so sorry.", "sad"),
    ]

    print("BMO Sentiment Analyzer — Test Run")
    print("=" * 50)
    all_pass = True
    for text, expected in test_cases:
        got = sa.analyze(text)
        status = "✓" if got == expected else "✗"
        if got != expected:
            all_pass = False
        print(f"{status} Expected={expected:<10} Got={got:<10} | {text[:50]}")

    print("=" * 50)
    print("All tests passed!" if all_pass else "Some tests failed — tune thresholds.")
