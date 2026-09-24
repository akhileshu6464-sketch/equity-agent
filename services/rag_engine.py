"""
Company-Isolated RAG Engine (services/rag_engine.py)
Enforces strict company-level partitioning for vector / semantic / text chunk retrieval.
Hard failure is triggered if any chunk from another company enters the context.
"""

import os
import re
import math
import sqlite3
import logging
from typing import List, Dict, Any, Optional

from core.research_context import ResearchRunContext, DataContaminationError, assert_company_boundary

logger = logging.getLogger("ResearchBeast.RAGEngine")

DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
RAG_DB_PATH = os.path.join(DEFAULT_DATA_DIR, "document_cache.db")


class CompanyRAGEngine:
    """
    RAG engine with strict company_id isolation.
    Guarantees that semantic / keyword retrieval filters explicitly by company_id.
    """

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path or RAG_DB_PATH
        self._init_db()

    def _init_db(self) -> None:
        """Initializes company-partitioned SQLite tables and indexes."""
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    isin TEXT,
                    company_name TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    period TEXT,
                    source TEXT NOT NULL,
                    source_url TEXT,
                    page_number INTEGER,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    doc_date TEXT,
                    period TEXT,
                    source TEXT,
                    page_number INTEGER,
                    chunk_index INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_company ON documents(company_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_company ON document_chunks(company_id)")

            # Automatic schema migration for existing SQLite databases
            for col, col_type in [
                ("doc_date", "TEXT"),
                ("period", "TEXT"),
                ("source", "TEXT"),
                ("page_number", "INTEGER")
            ]:
                try:
                    conn.execute(f"ALTER TABLE document_chunks ADD COLUMN {col} {col_type}")
                except sqlite3.OperationalError:
                    pass  # Column already exists

            conn.commit()
        finally:
            conn.close()

    def store_document_with_chunks(
        self,
        run_context: ResearchRunContext,
        document_id: str = "",
        document_type: str = "",
        content: str = "",
        source: str = "",
        source_url: str = "",
        period: str = "",
        page_number: int = 1,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        **kwargs
    ) -> int:
        """
        Stores an official document and its chunks strictly bound to run_context.company_id.
        """
        document_id = document_id or kwargs.get("doc_id", "")
        document_type = document_type or kwargs.get("doc_type", "")
        if not content or not content.strip():
            return 0

        # Validate that no conflicting company_id is provided
        foreign_cid = kwargs.get("company_id")
        if foreign_cid:
            run_context.assert_same_company(foreign_cid, caller_module="CompanyRAGEngine.store_document")
        assert_company_boundary(kwargs, run_context.company_id, caller_module="CompanyRAGEngine.store_document")

        conn = sqlite3.connect(self._db_path)
        chunks_count = 0
        now_ts = os.path.getmtime(self._db_path) if os.path.exists(self._db_path) else 0.0
        import time
        now_ts = time.time()

        try:
            # 1. Insert Document
            conn.execute("""
                INSERT OR REPLACE INTO documents (
                    document_id, company_id, ticker, isin, company_name,
                    document_type, period, source, source_url, page_number, content, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_id,
                run_context.company_id,
                run_context.ticker,
                run_context.isin,
                run_context.company_name,
                document_type,
                period,
                source,
                source_url,
                page_number,
                content,
                now_ts
            ))

            # 2. Chunk text
            text = content.strip()
            words = text.split()
            step = chunk_size - chunk_overlap
            if step <= 0:
                step = chunk_size

            raw_chunks = []
            for i in range(0, len(words), step):
                chunk_slice = " ".join(words[i:i + chunk_size])
                if len(chunk_slice.strip()) > 30:
                    raw_chunks.append(chunk_slice.strip())

            if not raw_chunks:
                raw_chunks = [text]

            # Delete any existing chunks for this document
            conn.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))

            for idx, chk_text in enumerate(raw_chunks):
                chunk_id = f"{document_id}_chk_{idx}"
                doc_date = kwargs.get("date") or kwargs.get("publication_date") or ""
                conn.execute("""
                    INSERT OR REPLACE INTO document_chunks (
                        chunk_id, document_id, company_id, ticker, document_type,
                        doc_date, period, source, page_number,
                        chunk_index, chunk_text, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk_id,
                    document_id,
                    run_context.company_id,
                    run_context.ticker,
                    document_type,
                    doc_date,
                    period,
                    source,
                    page_number,
                    idx,
                    chk_text,
                    now_ts
                ))
                chunks_count += 1

            conn.commit()
            logger.info(f"Stored document {document_id} ({document_type}) with {chunks_count} chunks for {run_context.company_id}")
        finally:
            conn.close()

        return chunks_count

    def retrieve_chunks(
        self,
        run_context: ResearchRunContext,
        query: str = "",
        document_types: Optional[List[str]] = None,
        limit: int = 6,
        top_k: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        RAG retrieval with STRICT company_id filtering (Section 9).
        Never retrieves chunks belonging to other companies.
        Enforces a HARD FAILURE assertion if any foreign company data is returned.
        Every returned chunk contains:
        company_id, document_id, document_type, date, period, source, page_or_chunk, chunk_text.
        """
        if top_k is not None:
            limit = top_k
        elif "k" in kwargs:
            limit = kwargs["k"]

        conn = sqlite3.connect(self._db_path)
        try:
            # Handle backward compatibility if table was created with older schema
            sql = """
                SELECT chunk_id, document_id, company_id, ticker, document_type,
                       chunk_index, chunk_text,
                       COALESCE(doc_date, '') as doc_date,
                       COALESCE(period, '') as period,
                       COALESCE(source, '') as source,
                       COALESCE(page_number, 1) as page_number
                FROM document_chunks
                WHERE company_id = ?
            """
            params = [run_context.company_id]

            if document_types:
                placeholders = ",".join("?" for _ in document_types)
                sql += f" AND document_type IN ({placeholders})"
                params.extend(document_types)

            cursor = conn.cursor()
            try:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
            except sqlite3.OperationalError:
                # Fallback if old SQLite schema without extra columns
                fallback_sql = "SELECT chunk_id, document_id, company_id, ticker, document_type, chunk_index, chunk_text FROM document_chunks WHERE company_id = ?"
                if document_types:
                    fallback_sql += f" AND document_type IN ({placeholders})"
                cursor.execute(fallback_sql, params)
                raw_rows = cursor.fetchall()
                rows = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], "", "", "", 1) for r in raw_rows]
        finally:
            conn.close()

        results = []
        for r in rows:
            chunk_obj = {
                "chunk_id": r[0],
                "document_id": r[1],
                "company_id": r[2],
                "ticker": r[3],
                "document_type": r[4],
                "chunk_index": r[5],
                "chunk_text": r[6],
                "content": r[6],
                "date": r[7],
                "period": r[8],
                "source": r[9],
                "page_number": r[10],
                "page_or_chunk": f"Page {r[10]} (Chunk {r[5]})" if r[10] else f"Chunk {r[5]}"
            }

            # HARD FAILURE CHECK (Section 9: zero cross-company leakage)
            if chunk_obj["company_id"] != run_context.company_id:
                raise DataContaminationError(
                    f"CRITICAL HARD FAILURE: RAG retrieval for company_id='{run_context.company_id}' "
                    f"returned chunk '{chunk_obj['chunk_id']}' belonging to foreign company '{chunk_obj['company_id']}'! "
                    f"Execution terminated immediately."
                )
            assert_company_boundary(chunk_obj, run_context.company_id, caller_module="CompanyRAGEngine.retrieve_chunks")

            results.append(chunk_obj)

        if not results or not query:
            return results[:limit]

        # BM25-style keyword relevance ranking across this company's chunks
        query_terms = [q.lower() for q in re.findall(r"\w+", query) if len(q) > 2]
        if not query_terms:
            return results[:limit]

        def score_chunk(chk: Dict[str, Any]) -> float:
            txt = chk["chunk_text"].lower()
            score = 0.0
            for term in query_terms:
                c = txt.count(term)
                if c > 0:
                    score += 1.0 + math.log(1.0 + c)
            return score

        scored_results = sorted(results, key=score_chunk, reverse=True)
        return scored_results[:limit]
