"""
Company-Scoped Concall Transcript Store (services/drishti/concall_store.py)
Stores and chunks conference call transcripts for company-isolated RAG retrieval.
Guarantees:
1. Every transcript chunk strictly carries company_id, document_id, quarter, date, and source="DRISHTI".
2. RAG search filters by company_id BEFORE matching to eliminate cross-company contamination.
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
from services.drishti.models import ConcallTranscriptChunk

logger = logging.getLogger("ResearchBeast.Drishti.ConcallStore")

TRANSCRIPT_STORE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "transcripts")


class ConcallStore:
    """In-memory and file-backed company-scoped conference call store."""

    def __init__(self, store_dir: str = TRANSCRIPT_STORE_DIR):
        self.store_dir = store_dir
        self._memory_chunks: Dict[str, List[ConcallTranscriptChunk]] = {}
        try:
            os.makedirs(self.store_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not initialize concall transcript store directory: {e}")

    @staticmethod
    def chunk_transcript(
        company_id: str,
        document_id: str,
        quarter: str,
        date: str,
        text: str,
        chunk_size_words: int = 250,
        overlap_words: int = 40
    ) -> List[ConcallTranscriptChunk]:
        """
        Splits transcript text into bounded chunks, strictly tagging each with canonical company_id.
        """
        if not text:
            return []

        words = text.split()
        chunks: List[ConcallTranscriptChunk] = []
        idx = 0
        step = max(chunk_size_words - overlap_words, 50)

        for i in range(0, len(words), step):
            chunk_words = words[i:i + chunk_size_words]
            chunk_text = " ".join(chunk_words).strip()
            if not chunk_text:
                continue

            chunk = ConcallTranscriptChunk(
                company_id=company_id,
                document_id=document_id,
                quarter=quarter,
                date=date,
                chunk_index=idx,
                text=chunk_text,
                source="DRISHTI"
            )
            chunks.append(chunk)
            idx += 1

        return chunks

    def add_transcript(
        self,
        company_id: str,
        document_id: str,
        quarter: str,
        date: str,
        text: str
    ) -> List[ConcallTranscriptChunk]:
        """
        Chunks and persists a company transcript.
        """
        chunks = self.chunk_transcript(company_id, document_id, quarter, date, text)
        if not chunks:
            return []

        if company_id not in self._memory_chunks:
            self._memory_chunks[company_id] = []
        self._memory_chunks[company_id].extend(chunks)

        # Persist to disk
        cid_clean = company_id.replace(":", "_").replace("/", "_")
        file_path = os.path.join(self.store_dir, f"{cid_clean}_{quarter}_{document_id}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([c.to_dict() for c in chunks], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Error persisting concall chunks to {file_path}: {e}")

        return chunks

    def retrieve_chunks(
        self,
        company_id: str,
        query: str,
        quarter: Optional[str] = None,
        top_k: int = 5
    ) -> List[ConcallTranscriptChunk]:
        """
        Retrieves relevant transcript chunks.
        MANDATORY: Filters by company_id BEFORE running lexical or semantic matching.
        """
        # 1. Strictly isolate candidate chunks by company_id
        candidate_chunks: List[ConcallTranscriptChunk] = []

        if company_id in self._memory_chunks:
            candidate_chunks = [c for c in self._memory_chunks[company_id] if c.company_id == company_id]
        else:
            # Load from disk
            cid_clean = company_id.replace(":", "_").replace("/", "_")
            for fname in os.listdir(self.store_dir):
                if fname.startswith(cid_clean) and fname.endswith(".json"):
                    try:
                        with open(os.path.join(self.store_dir, fname), "r", encoding="utf-8") as f:
                            raw_list = json.load(f)
                            for raw in raw_list:
                                if raw.get("company_id") == company_id:
                                    candidate_chunks.append(ConcallTranscriptChunk(**raw))
                    except Exception:
                        pass
            self._memory_chunks[company_id] = candidate_chunks

        # Filter by quarter if specified
        if quarter:
            candidate_chunks = [c for c in candidate_chunks if c.quarter.lower() == quarter.lower()]

        if not candidate_chunks or not query:
            return candidate_chunks[:top_k]

        # Lexical keyword score for relevance
        query_tokens = set(re.findall(r"\w+", query.lower()))
        scored_chunks = []
        for c in candidate_chunks:
            c_tokens = set(re.findall(r"\w+", c.text.lower()))
            overlap = len(query_tokens & c_tokens)
            scored_chunks.append((overlap, c))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c for score, c in scored_chunks[:top_k]]


# Global singleton
_CONCALL_STORE = ConcallStore()

def get_concall_store() -> ConcallStore:
    return _CONCALL_STORE
