import math
import re
from collections import Counter
from collections.abc import Sequence

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

def bm25_scores(
    query: str,
    corpus: Sequence[str],
    *,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[float]:
    """Compute BM25 scores for a query against an in-memory corpus.

    This is intentionally dependency-free for v0.2. Later we can replace this with
    PostgreSQL full-text search, pgvector hybrid search, or a dedicated search engine.
    """
    if not corpus:
        return []

    query_terms = tokenize(query)
    if not query_terms:
        return [0.0 for _ in corpus]

    tokenized_corpus = [tokenize(document) for document in corpus]
    doc_count = len(tokenized_corpus)
    doc_lengths = [len(tokens) for tokens in tokenized_corpus]
    avg_doc_len = sum(doc_lengths) / max(doc_count, 1)
    avg_doc_len = max(avg_doc_len, 1.0)

    document_frequencies: Counter[str] = Counter()
    for tokens in tokenized_corpus:
        document_frequencies.update(set(tokens))

    query_term_counts = Counter(query_terms)
    scores: list[float] = []

    for tokens, doc_len in zip(tokenized_corpus, doc_lengths, strict=True):
        term_frequencies = Counter(tokens)
        score = 0.0

        for term, query_tf in query_term_counts.items():
            tf = term_frequencies.get(term, 0)
            if tf == 0:
                continue

            df = document_frequencies.get(term, 0)
            idf = math.log(1 + (doc_count - df + 0.5) / (df + 0.5))
            length_norm = 1 - b + b * (doc_len / avg_doc_len)
            denominator = tf + k1 * length_norm
            score += idf * ((tf * (k1 + 1)) / denominator) * query_tf

        scores.append(round(score, 4))

    return scores
