"""Keyword matching: how many times a Data Type's keywords appear in a text, as whole words."""

import re

WORD_START = r"(?<![^\W_])"
WORD_END = r"(?![^\W_])"
WORD_GAP = r"[\W_]+"


def count_matches(keywords: list[str], text: str, case_sensitive: bool) -> int:
    return len(_pattern(keywords, case_sensitive).findall(text))


def _pattern(keywords: list[str], case_sensitive: bool) -> re.Pattern[str]:
    longest_first = sorted(keywords, key=len, reverse=True)
    alternatives = "|".join(_keyword_pattern(keyword) for keyword in longest_first)
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(f"{WORD_START}(?:{alternatives}){WORD_END}", flags)


def _keyword_pattern(keyword: str) -> str:
    return WORD_GAP.join(re.escape(word) for word in keyword.split())
