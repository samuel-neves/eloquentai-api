Simple FAQ loader that works without embedding APIs.
This creates a basic keyword-based search system that doesn't require
OpenAI or complex embedding models.

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import settings

def create_simple_faq_database():

    print("🚀 Simple FAQ Database Creator")
    print("=" * 50)
    print("This creates a keyword-based FAQ system without requiring")
    print("embeddings or external APIs.\n")

    data_file = Path(__file__).parent.parent / "data" / "fintech_faqs.json"

    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return False

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        
        return False

    faqs = data.get("fintech_faqs", [])
    if not faqs:
        print("❌ No FAQs found in the data file.")
        return False

    print(f"📋 Found {len(faqs)} FAQs to process...")

    search_db = {"faqs": [], "keyword_index": {}, "category_index": {}}

    for i, faq in enumerate(faqs):
        faq_entry = {
            "id": f"faq_{i+1:03d}",
            "category": faq["category"],
            "question": faq["question"],
            "answer": faq["answer"],
            "keywords": faq["keywords"],
        }
        search_db["faqs"].append(faq_entry)

        all_keywords = (
            faq["keywords"]
            + faq["question"].lower().split()
            + faq["answer"].lower().split()
        )
        for keyword in all_keywords:
            keyword = keyword.strip().lower()
            if len(keyword) > 2:
                if keyword not in search_db["keyword_index"]:
                    search_db["keyword_index"][keyword] = []
                search_db["keyword_index"][keyword].append(faq_entry["id"])

        category = faq["category"]
        if category not in search_db["category_index"]:
            search_db["category_index"][category] = []
        search_db["category_index"][category].append(faq_entry["id"])

    db_file = Path(__file__).parent.parent / "data" / "faq_search_db.json"
    try:
        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(search_db, f, indent=2, ensure_ascii=False)
        print(f"✅ FAQ search database created: {db_file}")
    except Exception as e:
        
        return False

    print(f"\n📊 Database Statistics:")
    print(f"   FAQs: {len(search_db['faqs'])}")
    print(f"   Categories: {len(search_db['category_index'])}")
    print(f"   Keywords: {len(search_db['keyword_index'])}")

    print(f"\n📋 Categories:")
    for category, faq_ids in search_db["category_index"].items():
        print(f"   - {category}: {len(faq_ids)} FAQs")

    return True

def create_simple_search_service():

    search_service_code = '''"""
Simple FAQ search service that works without embeddings.
This provides keyword-based search functionality.

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
                print(f"✅ FAQ search database loaded: {len(self.db['faqs'])} FAQs")
            else:
                print("❌ FAQ search database not found. Run load_faqs_simple.py first.")
                self.db = {"faqs": [], "keyword_index": {}, "category_index": {}}
        except Exception as e:
            
            self.db = {"faqs": [], "keyword_index": {}, "category_index": {}}
    
    def search(self, query: str, category: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
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
                scored_faqs.append({
                    "id": faq["id"],
                    "score": min(score / len(query_words), 1.0),
                    "content": f"Q: {faq['question']}\n\nA: {faq['answer']}",
                    "title": f"FAQ: {faq['question']}",
                    "metadata": faq
                })
        
        scored_faqs.sort(key=lambda x: x["score"], reverse=True)
        return scored_faqs[:top_k]
    
    def get_categories(self) -> List[str]:
        if not self.db:
            return []
        return list(self.db["category_index"].keys())
    
    def is_available(self) -> bool:
        return self.db is not None and len(self.db["faqs"]) > 0

    service_file = Path(__file__).parent.parent / "services" / "simple_faq_search.py"
    try:
        with open(service_file, "w", encoding="utf-8") as f:
            f.write(search_service_code)
        print(f"✅ Simple search service created: {service_file}")
        return True
    except Exception as e:
        
        return False

def main():
    print("Creating simple FAQ system that works without embeddings...\n")

    success1 = create_simple_faq_database()
    success2 = create_simple_search_service()

    if success1 and success2:
        print(f"\n🎉 Simple FAQ system created successfully!")
        print(f"\n🎯 Next steps:")
        print(f"1. This system works without OpenAI or Pinecone")
        print(f"2. Update your chat service to use SimpleFAQSearch when needed")
        print(f"3. Start your API: python3 main.py")
        print(f"4. Test with questions like 'How do I create account?'")

        print(f"\n💡 This is a working solution while you fix the embedding issues!")
        return 0
    else:
        print(f"\n❌ Failed to create simple FAQ system")
        return 1

if __name__ == "__main__":
    exit(main())
