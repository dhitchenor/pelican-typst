"""
#lorem(n) -- placeholder text drawn from a bundled word pool
(../data/lorem.txt, one level up from this package). Deterministic
wraparound through the pool, not a reproduction of Typst's own
seeded-random lorem() algorithm -- good enough for filler text.
"""

import os
import re

_LOREM_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "lorem.txt"
)
_lorem_words_cache = None


def _load_lorem_words():
    global _lorem_words_cache
    if _lorem_words_cache is None:
        try:
            with open(_LOREM_DATA_PATH, "r", encoding="utf-8") as f:
                text = f.read()
            _lorem_words_cache = re.findall(r"[A-Za-z]+", text.lower())
        except OSError:
            _lorem_words_cache = ["lorem", "ipsum", "dolor", "sit", "amet"]
    return _lorem_words_cache


def _generate_lorem(n):
    """Deterministic placeholder text: n words drawn (with wraparound)
    from a bundled classic Lorem Ipsum word pool. Not a faithful
    reproduction of Typst's own lorem() output (which uses a seeded
    seed for pseudo-random selection) -- just coherent-looking filler
    text of the requested rough length."""
    words = _load_lorem_words()
    if n <= 0 or not words:
        return ""
    pool_len = len(words)
    chosen = [words[i % pool_len] for i in range(n)]
    chosen[0] = chosen[0].capitalize()
    return " ".join(chosen) + "."
