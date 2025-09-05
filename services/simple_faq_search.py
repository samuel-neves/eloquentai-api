# Simple FAQ search service that works without embeddings.
# Provides keyword-based search functionality.

import json
from pathlib import Path
from typing import List, Dict, Any


class SimpleFAQSearch:
    def __init__(self):
        self.db = None
        self._load_database()

    def _load_database(self):
        try:
            db_file = Path(__file__).parent.parent / "data" / "faq_search_db.json"
            if db_file.exists():
                with open(db_file, "r", encoding="utf-8") as f:
                    self.db = json.load(f)
            else:
                self.db = {"faqs": [], "keyword_index": {}, "category_index": {}}
        except Exception:

            self.db = {"faqs": [], "keyword_index": {}, "category_index": {}}

    def search(
        self, query: str, category: str = None, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        if not self.db or not self.db["faqs"]:
            return []

        query_words = query.lower().split()
        scored_faqs = []

        if category:
            candidate_ids = self.db["category_index"].get(category, [])
            candidates = [faq for faq in self.db["faqs"] if faq["id"] in candidate_ids]
        else:
            candidates = self.db["faqs"]

        for faq in candidates:
            score = 0.0

            question_words = faq["question"].lower().split()
            for word in query_words:
                if any(word in q_word for q_word in question_words):
                    score += 2.0

            for word in query_words:
                if word in [kw.lower() for kw in faq["keywords"]]:
                    score += 1.5

            answer_words = faq["answer"].lower().split()
            for word in query_words:
                if any(word in a_word for a_word in answer_words):
                    score += 1.0

            if score > 0:
                scored_faqs.append(
                    {
                        "id": faq["id"],
                        "score": min(score / len(query_words), 1.0),
                        "content": f"Q: {faq['question']}\n\nA: {faq['answer']}",
                        "title": f"FAQ: {faq['question']}",
                        "metadata": faq,
                    }
                )

        scored_faqs.sort(key=lambda x: x["score"], reverse=True)
        return scored_faqs[:top_k]

    def get_categories(self) -> List[str]:
        if not self.db:
            return []
        return list(self.db["category_index"].keys())

    def is_available(self) -> bool:
        return self.db is not None and len(self.db["faqs"]) > 0
