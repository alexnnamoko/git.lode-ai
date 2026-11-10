"""Conservative lexical retrieval for bundled BS 8110 research datasets.

Retrieval relevance is not a probability, engineering confidence, or proof that a
record accurately represents the published standard.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
STOP_WORDS = {
    "the", "and", "for", "with", "from", "what", "when", "where", "which",
    "how", "does", "can", "are", "is", "in", "of", "to", "a", "an",
    "on", "by", "be", "it", "this", "that", "explain", "please",
}
TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9.]*|\d+(?:\.\d+)*")
CLAUSE_PATTERN = re.compile(r"\b(?:clause\s*)?(\d+(?:\.\d+){1,3})\b", re.IGNORECASE)


def load(name: str) -> list[dict[str, Any]]:
    """Load a bundled JSON dataset; return an empty list for unavailable data."""
    try:
        data = json.loads((ROOT / name).read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _tokens(value: Any) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(str(value))
            if len(token) > 1 and token.lower() not in STOP_WORDS]


def _normalise_clause(value: Any) -> str:
    """Normalise a clause label without interpreting other numeric values."""
    match = CLAUSE_PATTERN.search(str(value or ""))
    return match.group(1) if match else str(value or "").strip()


def _query_clause(query: str) -> str | None:
    match = CLAUSE_PATTERN.search(query or "")
    return match.group(1) if match else None


def search_knowledge(
    query: str,
    limit: int = 8,
    *,
    clause: str | None = None,
    member_type: str | None = None,
    topic: str | None = None,
) -> list[dict[str, Any]]:
    """Return BM25-style lexical matches with explicit source provenance.

    Optional filters are strict. An explicit clause in the query receives an exact
    clause boost; it is not treated as proof that the record is applicable.
    """
    if int(limit) <= 0:
        return []
    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    requested_clause = _normalise_clause(clause) if clause else _query_clause(query)
    records: list[tuple[str, dict[str, Any], list[str], str]] = []
    fields_by_kind = {
        "rule": ("rule_id", "clause", "topic", "member_type", "applicability", "inputs", "formula", "outputs", "limits", "cross_refs"),
        "qa": ("type", "clause", "question", "answer"),
    }
    for kind, filename in (
        ("rule", "bs8110_beam_design_rules.json"),
        ("qa", "bs8110_qa_dataset.json"),
    ):
        for record in load(filename):
            if requested_clause and _normalise_clause(record.get("clause")) != requested_clause:
                # A clause explicitly requested by the user is a strict filter.
                # It is safer to return no match than an unrelated clause.
                continue
            if member_type and kind == "rule":
                record_member = str(record.get("member_type", "")).strip().lower()
                if record_member not in {str(member_type).strip().lower(), "general"}:
                    continue
            if topic:
                record_topic = str(record.get("topic", record.get("type", ""))).strip().lower()
                if record_topic != str(topic).strip().lower():
                    continue
            text = " ".join(str(record.get(field, "")) for field in fields_by_kind[kind])
            tokens = _tokens(text)
            if tokens:
                records.append((kind, record, tokens, text.lower()))

    if not records:
        return []

    document_frequency: Counter[str] = Counter()
    for _, _, tokens, _ in records:
        document_frequency.update(set(tokens))
    n_docs = len(records)
    average_length = sum(len(tokens) for _, _, tokens, _ in records) / max(1, n_docs)
    query_counts = Counter(query_tokens)
    query_phrase = " ".join(query_tokens)
    ranked: list[tuple[float, str, dict[str, Any]]] = []

    # BM25 parameters are conventional ranking settings, not model confidence.
    k1, b = 1.5, 0.75
    for kind, record, tokens, text in records:
        counts = Counter(tokens)
        doc_length = len(tokens)
        score = 0.0
        for token, q_count in query_counts.items():
            frequency = counts[token]
            if not frequency:
                continue
            idf = math.log(1 + (n_docs - document_frequency[token] + 0.5) /
                           (document_frequency[token] + 0.5))
            denominator = frequency + k1 * (1 - b + b * doc_length / max(1.0, average_length))
            score += idf * (frequency * (k1 + 1) / denominator) * min(q_count, 2)

        if query_phrase and query_phrase in text:
            score += 2.0
        if requested_clause and _normalise_clause(record.get("clause")) == requested_clause:
            score += 8.0
        if kind == "qa" and any(token in _tokens(record.get("question", "")) for token in query_tokens):
            score += 0.35
        if score > 0:
            ranked.append((score, kind, record))

    ranked.sort(key=lambda item: (-item[0], item[1], str(item[2].get("clause", ""))))
    results = []
    for score, kind, record in ranked[:int(limit)]:
        dataset = "bs8110_beam_design_rules.json" if kind == "rule" else "bs8110_qa_dataset.json"
        results.append({
            "score": round(score, 3),
            "score_type": "lexical_relevance_not_confidence",
            "type": kind,
            "record": record,
            "source": {
                "code": record.get("code", "BS 8110-1:1997 (dataset label; verify original source)"),
                "clause": record.get("clause"),
                "record_id": record.get("rule_id", record.get("id")),
                "dataset": dataset,
                "source_status": "Bundled research dataset; not independently verified against the complete standard",
            },
        })
    return results


def readable_record(hit: dict[str, Any]) -> dict[str, Any]:
    """Convert a retrieval result into a display-safe, provenance-aware record."""
    record = hit["record"]
    kind = hit["type"]
    source = hit.get("source", {})
    if kind == "qa":
        return {
            "kind": "Question & answer",
            "title": record.get("question") or "Knowledge entry",
            "reference": record.get("clause") or "Reference not supplied",
            "explanation": record.get("answer") or "The supplied dataset contains no answer text for this entry.",
            "formula": None,
            "applicability": None,
            "limits": None,
            "source_id": record.get("id"),
            "source_code": source.get("code", record.get("code", "BS 8110-1:1997 dataset label")),
            "dataset": source.get("dataset", "unknown dataset"),
            "source_status": source.get("source_status", "Dataset provenance unavailable"),
        }
    return {
        "kind": "Design rule",
        "title": str(record.get("topic") or record.get("rule_id") or "Design rule").replace("_", " ").title(),
        "reference": record.get("clause") or "Clause reference not supplied",
        "explanation": record.get("formula") or "The supplied rule record does not contain explanatory text.",
        "formula": record.get("formula"),
        "applicability": record.get("applicability") or [],
        "inputs": record.get("inputs") or [],
        "outputs": record.get("outputs") or [],
        "limits": record.get("limits") or {},
        "cross_references": record.get("cross_refs") or [],
        "source_id": record.get("rule_id"),
        "source_code": source.get("code", record.get("code", "BS 8110-1:1997 dataset label")),
        "dataset": source.get("dataset", "unknown dataset"),
        "source_status": source.get("source_status", "Dataset provenance unavailable"),
    }


def format_retrieval_context(hits: list[dict[str, Any]], max_chars: int = 10000) -> str:
    """Format retrieved records as bounded, clearly unverified reference material."""
    if not hits:
        return "No supporting BS 8110 dataset records were retrieved for this question."
    blocks = []
    for index, hit in enumerate(hits, start=1):
        item = readable_record(hit)
        blocks.append(
            f"SOURCE {index}\n"
            f"Type: {item['kind']}\n"
            f"Source label: {item['source_code']}\n"
            f"Clause as recorded in dataset: {item['reference']}\n"
            f"Dataset file: {item['dataset']}\n"
            f"Record identifier: {item['source_id']}\n"
            f"Title/question: {item['title']}\n"
            f"Record content: {item['explanation']}\n"
            f"Retrieval relevance score: {hit['score']} (not confidence)\n"
            "Source status: research dataset; verify wording and applicability in the published standard and amendments."
        )
    text = "\n\n---\n\n".join(blocks)
    return text[:max_chars]
