"""
Local, privacy-preserving technical documentation retrieval (RAG) engine for EmbeddedCoder AI.
Indexes local datasheets, register manuals, headers, and device trees without cloud dependence.
"""

import math
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class DocumentPassage:
    def __init__(
        self,
        doc_id: str,
        file_path: str,
        section: str,
        start_line: int,
        end_line: int,
        content: str,
    ):
        self.doc_id = doc_id
        self.file_path = file_path
        self.section = section
        self.start_line = start_line
        self.end_line = end_line
        self.content = content

    def citation(self) -> str:
        return f"[Doc: {self.doc_id} | File: {Path(self.file_path).name}:{self.start_line}-{self.end_line} | Section: {self.section}]"


class LocalDocIndexer:
    """
    Lightweight, deterministic BM25 documentation indexer for embedded engineering docs.
    Operates 100% locally with zero cloud dependencies.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.passages: List[DocumentPassage] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.vocab: Dict[str, int] = {}
        self.passage_tokens: List[List[str]] = []

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Normalize and tokenize technical documentation text."""
        # Retain alphanumeric and underscores (for register and variable names)
        tokens = re.findall(r"[A-Za-z0-9_]{2,}", text.lower())
        return tokens

    def add_document(self, file_path: Path, doc_id: Optional[str] = None, chunk_lines: int = 30) -> int:
        """Parse and chunk a local technical file into searchable passages."""
        if not file_path.exists():
            return 0

        doc_id = doc_id or file_path.stem
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return 0

        lines = content.splitlines()
        chunks_added = 0
        current_section = "General"

        for i in range(0, len(lines), chunk_lines):
            chunk_slice = lines[i : i + chunk_lines]
            chunk_text = "\n".join(chunk_slice).strip()
            if not chunk_text or len(chunk_text) < 20:
                continue

            # Detect section header if present (e.g. ## Register Map or /* Header */)
            for line in chunk_slice:
                if line.strip().startswith(("#", "//", "/*", "SECTION:")):
                    current_section = line.strip().lstrip("#/* ").rstrip("*/")
                    break

            passage = DocumentPassage(
                doc_id=doc_id,
                file_path=str(file_path),
                section=current_section,
                start_line=i + 1,
                end_line=min(i + chunk_lines, len(lines)),
                content=chunk_text,
            )
            self.passages.append(passage)
            tokens = self.tokenize(chunk_text)
            self.passage_tokens.append(tokens)
            self.doc_lengths.append(len(tokens))
            chunks_added += 1

        self._recompute_statistics()
        return chunks_added

    def _recompute_statistics(self):
        """Update corpus statistics for BM25 ranking."""
        total_docs = len(self.passages)
        if total_docs == 0:
            return

        self.avg_doc_len = sum(self.doc_lengths) / total_docs
        self.doc_freqs = {}

        for tokens in self.passage_tokens:
            unique_terms = set(tokens)
            for term in unique_terms:
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[DocumentPassage, float]]:
        """Retrieve most relevant technical passages for a given query."""
        query_tokens = self.tokenize(query)
        if not query_tokens or not self.passages:
            return []

        scores: List[float] = [0.0] * len(self.passages)
        total_docs = len(self.passages)

        for term in query_tokens:
            if term not in self.doc_freqs:
                continue

            # Inverse Document Frequency (IDF)
            df = self.doc_freqs[term]
            idf = math.log(1.0 + (total_docs - df + 0.5) / (df + 0.5))

            for idx, tokens in enumerate(self.passage_tokens):
                tf = tokens.count(term)
                if tf == 0:
                    continue

                doc_len = self.doc_lengths[idx]
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                score = idf * (tf * (self.k1 + 1.0)) / denom
                scores[idx] += score

        ranked = sorted(
            [(self.passages[i], scores[i]) for i in range(len(scores)) if scores[i] > 0.0],
            key=lambda x: x[1],
            reverse=True,
        )
        return ranked[:top_k]

    def format_grounded_prompt(self, query: str, top_k: int = 3) -> Tuple[str, List[str]]:
        """Construct prompt with explicit retrieved documentation citations."""
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return query, []

        context_blocks = []
        citations = []
        for passage, score in results:
            cit = passage.citation()
            citations.append(cit)
            context_blocks.append(f"--- TECHNICAL DOCUMENTATION PASSAGE {cit} ---\n{passage.content}")

        context_str = "\n\n".join(context_blocks)
        prompt = (
            f"Use the verified technical documentation below to answer the engineering inquiry.\n"
            f"If the answer is not contained in the documentation, explicitly state that evidence is insufficient.\n\n"
            f"{context_str}\n\n"
            f"--- INQUIRY ---\n{query}"
        )
        return prompt, citations
