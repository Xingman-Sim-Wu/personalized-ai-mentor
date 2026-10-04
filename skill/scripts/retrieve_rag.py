#!/usr/bin/env python3
"""Retrieve a small, provenance-preserving candidate set from the AW corpus."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = SKILL_ROOT / "references" / "rag-index.json"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for",
    "from", "had", "has", "have", "he", "her", "his", "i", "in", "into", "is",
    "it", "its", "not", "of", "on", "or", "our", "she", "that", "the", "their",
    "them", "they", "this", "to", "was", "were", "what", "when", "which", "while",
    "who", "with", "would", "wang", "alexandr",
}

NORMALIZATION = {
    "commitments": "commitment",
    "expanding": "expansion",
    "expanded": "expansion",
    "expand": "expansion",
    "growth": "expansion",
    "priorities": "priority",
    "prioritization": "priority",
    "projects": "project",
}

TYPE_BOOST = {
    "direct_statement": 1.35,
    "source_summary": 1.00,
    "source_record": 0.90,
    "derived_interpretation": 0.72,
    "interviewer_premise": 0.45,
}

STATUS_BOOST = {
    "keep": 1.00,
    "keep_with_caveat": 0.92,
    "keep_scope_restricted": 0.88,
    "keep_narrow": 0.80,
    "keep_as_pacing_counterevidence": 0.90,
    "keep_with_transcript_caveat": 0.82,
    "downgrade_pending_transcript": 0.55,
}


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower().replace("over-hiring", "overhiring hiring"))
    return [NORMALIZATION.get(word, word) for word in words if len(word) > 1 and word not in STOPWORDS]


def load_index() -> dict:
    if not INDEX_PATH.exists():
        raise SystemExit(f"Missing index: {INDEX_PATH}. Run scripts/build_rag_index.py first.")
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def candidate_scores(index: dict, query: str) -> list[dict]:
    chunks = index["chunks"]
    query_terms = list(dict.fromkeys(tokenize(query)))
    if not query_terms:
        return []
    document_frequency = Counter()
    for chunk in chunks:
        available = set(chunk["term_frequency"])
        for term in query_terms:
            if term in available:
                document_frequency[term] += 1
    average_length = sum(chunk["document_length"] for chunk in chunks) / max(len(chunks), 1)
    scored = []
    for chunk in chunks:
        tf = chunk["term_frequency"]
        matched = [term for term in query_terms if term in tf]
        matched_content = [term for term in matched if term in chunk.get("content_terms", [])]
        minimum_overlap = 1 if len(query_terms) <= 3 else 2
        if len(matched) < minimum_overlap or not matched_content:
            continue
        score = 0.0
        for term in query_terms:
            frequency = tf.get(term, 0)
            if not frequency:
                continue
            df = document_frequency[term]
            idf = math.log(1 + (len(chunks) - df + 0.5) / (df + 0.5))
            k1, b = 1.5, 0.75
            denominator = frequency + k1 * (1 - b + b * chunk["document_length"] / average_length)
            score += idf * (frequency * (k1 + 1)) / denominator
        score *= TYPE_BOOST.get(chunk["statement_type"], 0.80)
        score *= STATUS_BOOST.get(chunk["source_status"], 0.75)
        item = {key: value for key, value in chunk.items() if key not in {"term_frequency", "document_length"}}
        item["score"] = round(score, 4)
        item["matched_terms"] = matched
        item["matched_content_terms"] = matched_content
        scored.append(item)
    return sorted(scored, key=lambda item: (-item["score"], item["chunk_id"]))


def term_set(item: dict) -> set[str]:
    return set(tokenize(item["text"]))


def deduplicate(candidates: list[dict], max_results: int, min_score: float) -> list[dict]:
    selected: list[dict] = []
    for candidate in candidates:
        if candidate["score"] < min_score:
            continue
        candidate_terms = term_set(candidate)
        redundant = False
        for existing in selected:
            existing_terms = term_set(existing)
            union = candidate_terms | existing_terms
            similarity = len(candidate_terms & existing_terms) / len(union) if union else 0
            if similarity >= 0.72:
                redundant = True
                break
        if not redundant:
            selected.append(candidate)
        if len(selected) >= max_results:
            break
    return selected


def retrieve(query: str, max_results: int = 4, min_score: float = 1.0) -> list[dict]:
    index = load_index()
    return deduplicate(candidate_scores(index, query), max_results=max_results, min_score=min_score)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True, help="Focused conceptual retrieval query")
    parser.add_argument("--max-results", type=int, default=4, choices=range(1, 6))
    parser.add_argument("--min-score", type=float, default=1.0)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    results = retrieve(args.query, args.max_results, args.min_score)
    if args.json:
        print(json.dumps({"query": args.query, "result_count": len(results), "results": results}, indent=2, ensure_ascii=False))
        return
    if not results:
        print("No sufficiently relevant Wang-source evidence found. Continue with the behavioral model.")
        return
    for result in results:
        print(f"[{result['source_id']}] {result['chunk_id']} | {result['statement_type']} | score={result['score']}")
        print(f"Source: {result['title']}")
        print(f"Matched: {', '.join(result['matched_terms'])}")
        print(result["text"])
        print()


if __name__ == "__main__":
    main()
