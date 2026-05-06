import re
from collections import Counter

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def keyword_score(query: str, content: str) -> float:
    query_terms = Counter(tokenize(query))
    content_terms = Counter(tokenize(content))
    if not query_terms:
        return 0.0
    overlap = sum(min(count, content_terms.get(term, 0)) for term, count in query_terms.items())
    return round(overlap / max(sum(query_terms.values()), 1), 4)

# TODO: Implement real BM25 with corpus-level document frequencies and field-aware weighting.
