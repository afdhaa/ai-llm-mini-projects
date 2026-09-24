import json
from pathlib import Path
from typing import Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from schema import TicketEvidence


class TicketRetriever:
    """Semantic & contextual retriever for unstructured customer support tickets."""

    def __init__(self, data_path: Path | str | None = None):
        if data_path is None:
            data_path = Path(__file__).resolve().parents[1] / "data" / "support_tickets.json"
        self.data_path = Path(data_path)
        self.tickets: list[dict[str, Any]] = self._load_data()
        self._vectorizer: TfidfVectorizer | None = None
        self._tfidf_matrix = None
        self._build_index()

    def _load_data(self) -> list[dict[str, Any]]:
        if not self.data_path.exists():
            return []
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_index(self):
        """Build TF-IDF vector space for semantic similarity searches."""
        if not self.tickets:
            return
        corpus = [
            f"{t.get('subject', '')} {t.get('message', '')} {t.get('category', '')}"
            for t in self.tickets
        ]
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._tfidf_matrix = self._vectorizer.fit_transform(corpus)

    def get_customer_tickets(self, customer: str) -> list[dict[str, Any]]:
        """Get all tickets for a specific customer, sorted newest first."""
        matched = [t for t in self.tickets if t.get("customer", "").lower() == customer.lower()]
        return sorted(matched, key=lambda x: x.get("timestamp", ""), reverse=True)

    def search_similar_tickets(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Perform semantic similarity search across all tickets in the corpus."""
        if not self.tickets or self._vectorizer is None or self._tfidf_matrix is None:
            return []

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._tfidf_matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0.05:  # Relevance threshold
                item = dict(self.tickets[idx])
                item["similarity_score"] = round(float(scores[idx]), 3)
                results.append(item)
        return results

    def retrieve_context(
        self,
        customer: str,
        focus_query: str = "churn risk complaint technical issue pricing cancellation",
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve most critical and relevant tickets for a target customer."""
        customer_tickets = self.get_customer_tickets(customer)
        if not customer_tickets:
            return []

        if len(customer_tickets) <= top_k:
            return customer_tickets

        # If customer has many tickets, rank by semantic relevance to churn indicators
        if self._vectorizer is not None:
            corpus = [
                f"{t.get('subject', '')} {t.get('message', '')} {t.get('category', '')}"
                for t in customer_tickets
            ]
            doc_vecs = self._vectorizer.transform(corpus)
            query_vec = self._vectorizer.transform([focus_query])
            scores = cosine_similarity(query_vec, doc_vecs).flatten()
            ranked_indices = np.argsort(scores)[::-1][:top_k]
            return [customer_tickets[i] for i in ranked_indices]

        return customer_tickets[:top_k]

    @staticmethod
    def format_ticket_evidence(ticket: dict[str, Any], sentiment: str = "CONCERNED") -> TicketEvidence:
        """Helper to convert ticket dict to TicketEvidence Pydantic model."""
        return TicketEvidence(
            ticket_id=ticket.get("ticket_id", "UNKNOWN"),
            channel=ticket.get("channel", "Unknown"),
            timestamp=ticket.get("timestamp", ""),
            snippet=f"[{ticket.get('subject', '')}] {ticket.get('message', '')[:180]}...",
            sentiment=sentiment,
        )
