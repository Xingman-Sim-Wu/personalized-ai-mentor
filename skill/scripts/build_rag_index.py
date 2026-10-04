#!/usr/bin/env python3
"""Build a deterministic local sparse index from the frozen AW source records."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = SKILL_ROOT / "references" / "sources"
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

NON_EVIDENCE_SECTIONS = {"topics", "potential persona dimensions", "provenance", "provenance and restriction"}


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower().replace("over-hiring", "overhiring hiring"))
    return [NORMALIZATION.get(word, word) for word in words if len(word) > 1 and word not in STOPWORDS]


def parse_scalar(value: str):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    _, raw, body = text.split("---\n", 2)
    metadata: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = parse_scalar(value)
    return metadata, body


def parse_sections(body: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    heading = "source_record"
    buffer: list[str] = []
    for line in body.splitlines():
        match = re.match(r"^(#{2,3})\s+(.+?)\s*$", line)
        if match:
            if any(part.strip() for part in buffer):
                sections.append((heading, "\n".join(buffer).strip()))
            heading = match.group(2).strip()
            buffer = []
        else:
            buffer.append(line)
    if any(part.strip() for part in buffer):
        sections.append((heading, "\n".join(buffer).strip()))
    return sections


def list_items(section_text: str) -> list[str]:
    return [line[2:].strip() for line in section_text.splitlines() if line.startswith("- ")]


def statement_type(heading: str) -> str:
    lowered = heading.lower()
    if "direct statements" in lowered:
        return "direct_statement"
    if "interviewer" in lowered:
        return "interviewer_premise"
    if "derived" in lowered:
        return "derived_interpretation"
    if "source notes" in lowered:
        return "source_summary"
    return "source_record"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "section"


def paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text)
    cleaned = []
    for part in parts:
        value = re.sub(r"\s+", " ", part).strip()
        if value:
            cleaned.append(value)
    return cleaned


def build_index() -> dict:
    chunks: list[dict] = []
    sources: list[dict] = []
    for path in sorted(SOURCE_DIR.glob("AW_*.md")):
        raw = path.read_text(encoding="utf-8")
        metadata, body = split_frontmatter(raw)
        sections = parse_sections(body)
        section_map = {heading.lower(): text for heading, text in sections}
        topics = list_items(section_map.get("topics", ""))
        dimensions = list_items(section_map.get("potential persona dimensions", ""))
        source_id = metadata.get("source_id", path.name.split("_", 2)[0])
        source_record = {
            "source_id": source_id,
            "path": str(path.relative_to(SKILL_ROOT)),
            "title": metadata.get("title", ""),
            "source_type": metadata.get("source_type", ""),
            "evidence_level": metadata.get("evidence_level", ""),
            "status": metadata.get("status", ""),
            "url": metadata.get("url", metadata.get("video_url", metadata.get("transcript_url", ""))),
            "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        }
        sources.append(source_record)

        for heading, section_text in sections:
            if heading.lower() in NON_EVIDENCE_SECTIONS:
                continue
            for sequence, paragraph in enumerate(paragraphs(section_text), start=1):
                if len(tokenize(paragraph)) < 5:
                    continue
                content_text = " ".join([heading, paragraph])
                retrieval_text = " ".join([content_text, " ".join(topics), " ".join(dimensions)])
                content_terms = tokenize(content_text)
                terms = tokenize(retrieval_text)
                chunks.append({
                    "chunk_id": f"{source_id}::{slugify(heading)}::{sequence:02d}",
                    "source_id": source_id,
                    "source_path": source_record["path"],
                    "title": source_record["title"],
                    "source_type": source_record["source_type"],
                    "evidence_level": source_record["evidence_level"],
                    "source_status": source_record["status"],
                    "source_url": source_record["url"],
                    "section": heading,
                    "statement_type": statement_type(heading),
                    "topics": topics,
                    "persona_dimensions": dimensions,
                    "text": paragraph,
                    "content_terms": sorted(set(content_terms)),
                    "term_frequency": dict(sorted(Counter(terms).items())),
                    "document_length": len(terms),
                })

    return {
        "schema_version": "0.1",
        "index_method": "local_sparse_bm25",
        "corpus_status": "frozen_at_aw_012",
        "source_count": len(sources),
        "chunk_count": len(chunks),
        "sources": sources,
        "chunks": chunks,
    }


def main() -> None:
    index = build_index()
    INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Indexed {index['source_count']} sources and {index['chunk_count']} chunks -> {INDEX_PATH}")


if __name__ == "__main__":
    main()
