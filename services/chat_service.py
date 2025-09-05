import openai
from typing import List, Dict, Any
from config import settings
from services.pinecone_service import PineconeService
from services.simple_faq_search import SimpleFAQSearch
import uuid


class ChatService:
    def __init__(self):
        self.client = None
        self.pinecone_service = PineconeService()
        self.simple_faq_search = SimpleFAQSearch()
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        self._initialized = False
        self._initialization_error = None

    def _initialize(self):
        if self._initialized:
            return self._initialization_error is None

        try:
            if (
                not settings.openai_api_key
                or settings.openai_api_key == "sk-your-openai-api-key-here"
            ):
                raise Exception("OpenAI API key not configured")

            self.client = openai.OpenAI(api_key=settings.openai_api_key)
            self._initialized = True
            self._initialization_error = None
            return True

        except Exception as e:
            self._initialization_error = str(e)
            self._initialized = True
            return False

    def generate_conversation_id(self) -> str:
        return str(uuid.uuid4())

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        return self.conversations.get(conversation_id, [])

    def add_to_conversation(self, conversation_id: str, role: str, content: str):
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        self.conversations[conversation_id].append({"role": role, "content": content})

    def retrieve_relevant_context(self, query: str, top_k: int = 5) -> dict:
        try:
            if self.pinecone_service.is_available():
                documents = self.pinecone_service.search_similar_documents(query, top_k)
                if documents:
                    documents = documents
                else:
                    return self._use_simple_faq_search(query, top_k)
            else:
                return self._use_simple_faq_search(query, top_k)

            if not documents:
                return {"context": "", "sources": [], "categories": []}

            context_parts = []
            sources = []
            categories = []

            for doc in documents:
                score_threshold = (
                    0.6 if doc.get("metadata", {}).get("faq_type") == "fintech" else 0.7
                )

                if doc["score"] > score_threshold:
                    metadata = doc.get("metadata", {})

                    if metadata.get("faq_type") == "fintech":
                        context_part = (
                            f"Q: {metadata.get('question', doc['title'])}\n\n"
                            f"A: {metadata.get('answer', doc.get('content', ''))}"
                        )
                        source_title = f"FAQ: {metadata.get('question', doc['title'])}"
                        category = metadata.get("category", "General")
                    else:
                        context_part = (
                            f"Source: {doc['title']}\nContent: {doc['content']}"
                        )
                        source_title = doc["title"]
                        category = "Document"

                    context_parts.append(context_part)
                    sources.append(source_title)
                    if category not in categories:
                        categories.append(category)

            return {
                "context": "\n\n---\n\n".join(context_parts),
                "sources": sources,
                "categories": categories,
            }

        except Exception as e:

            return {"context": "", "sources": [], "categories": []}

    def generate_response(
        self, message: str, conversation_id: str = None
    ) -> Dict[str, Any]:
        if not self._initialize():
            raise Exception(
                f"ChatService not initialized: {self._initialization_error}"
            )

        try:
            if not conversation_id:
                conversation_id = self.generate_conversation_id()

            rag_result = self.retrieve_relevant_context(message)
            context = rag_result["context"]
            context_sources = rag_result["sources"]
            context_categories = rag_result["categories"]

            history = self.get_conversation_history(conversation_id)

            system_message = self._create_fintech_system_message(
                context, context_categories
            )

            messages = [system_message]

            messages.extend(history[-10:])

            messages.append({"role": "user", "content": message})

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
            )

            ai_response = response.choices[0].message.content

            self.add_to_conversation(conversation_id, "user", message)
            self.add_to_conversation(conversation_id, "assistant", ai_response)

            sources = context_sources

            return {
                "response": ai_response,
                "conversation_id": conversation_id,
                "sources": sources,
            }

        except Exception as e:

            raise e

    def clear_conversation(self, conversation_id: str) -> bool:
        try:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
                return True
            return False
        except Exception as e:

            return False

    def _use_simple_faq_search(self, query: str, top_k: int = 5) -> dict:
        try:
            if not self.simple_faq_search.is_available():
                return {"context": "", "sources": [], "categories": []}

            documents = self.simple_faq_search.search(query, top_k=top_k)

            if not documents:
                return {"context": "", "sources": [], "categories": []}

            context_parts = []
            sources = []
            categories = []

            for doc in documents:
                if doc["score"] > 0.1:
                    metadata = doc.get("metadata", {})

                    context_part = (
                        f"Q: {metadata.get('question', doc['title'])}\n\n"
                        f"A: {metadata.get('answer', doc.get('content', ''))}"
                    )
                    source_title = f"FAQ: {metadata.get('question', doc['title'])}"
                    category = metadata.get("category", "General")

                    context_parts.append(context_part)
                    sources.append(source_title)
                    if category not in categories:
                        categories.append(category)

            return {
                "context": "\n\n---\n\n".join(context_parts),
                "sources": sources,
                "categories": categories,
            }

        except Exception as e:

            return {"context": "", "sources": [], "categories": []}

    def _create_fintech_system_message(self, context: str, categories: list) -> dict:
        base_prompt = (
            "You are EloquentAI, a fintech support assistant. Provide clear,"
            " accurate answers about accounts, payments, security, compliance,"
            " and troubleshooting. If you are not certain, state assumptions and"
            " suggest contacting support for account-specific issues."
        )

        if context:
            context_note = (
                f"\n\nRelevant information from our knowledge base:\n{context}"
            )
            if categories:
                context_note += f"\n\nThis information comes from the following categories: {', '.join(categories)}"
            context_note += "\n\nUse this information to provide accurate, specific answers. If the information doesn't fully address the question, supplement with general knowledge but clearly indicate when you're doing so."
        else:
            context_note = "\n\nNo specific information found in the knowledge base for this query. Provide helpful general information but recommend contacting customer support for account-specific or policy-specific questions."

        return {"role": "system", "content": base_prompt + context_note}

    def get_fintech_categories(self) -> list:
        return [
            "Account & Registration",
            "Payments & Transactions",
            "Security & Fraud Prevention",
            "Regulations & Compliance",
            "Technical Support & Troubleshooting",
        ]

    def is_available(self) -> bool:
        return self._initialize()
