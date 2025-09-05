from pinecone import Pinecone
from typing import List, Dict, Any
import openai
from config import settings
import uuid

class PineconeService:
    def __init__(self):
        self.pc = None
        self.index = None
        self.client = None
        self.index_name = settings.pinecone_index_name
        self._initialized = False
        self._initialization_error = None

    def _initialize(self):
        if self._initialized:
            return self._initialization_error is None

        try:
            if (
                not settings.pinecone_api_key
                or settings.pinecone_api_key == "your-pinecone-api-key-here"
            ):
                raise Exception("Pinecone API key not configured")

            if (
                not settings.openai_api_key
                or settings.openai_api_key == "sk-your-openai-api-key-here"
            ):
                raise Exception("OpenAI API key not configured")

            self.pc = Pinecone(api_key=settings.pinecone_api_key)
            self.index = self.pc.Index(self.index_name)

            openai.api_key = settings.openai_api_key
            self.client = openai.OpenAI(api_key=settings.openai_api_key)

            self._initialized = True
            self._initialization_error = None
            return True

        except Exception as e:
            self._initialization_error = str(e)
            self._initialized = True
            
            return False

    def get_embedding(self, text: str) -> List[float]:
        if not self._initialize():
            print(f"PineconeService not initialized: {self._initialization_error}")
            return []

        try:
            response = self.client.embeddings.create(
                input=text, model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except Exception as e:
            
            return []

    def store_document(
        self, content: str, title: str, metadata: Dict[str, Any] = None
    ) -> str:
        if not self._initialize():
            raise Exception(
                f"PineconeService not initialized: {self._initialization_error}"
            )

        try:
            embedding = self.get_embedding(content)

            if not embedding:
                raise Exception("Failed to generate embedding")

            doc_id = str(uuid.uuid4())

            doc_metadata = {"title": title, "content": content, **(metadata or {})}

            self.index.upsert(vectors=[(doc_id, embedding, doc_metadata)])

            return doc_id

        except Exception as e:
            
            raise e

    def search_similar_documents(
        self, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        if not self._initialize():
            print(f"PineconeService not initialized: {self._initialization_error}")
            return []

        try:
            query_embedding = self.get_embedding(query)

            if not query_embedding:
                return []

            results = self.index.query(
                vector=query_embedding, top_k=top_k, include_metadata=True
            )

            documents = []
            for match in results.matches:
                documents.append(
                    {
                        "id": match.id,
                        "score": match.score,
                        "content": match.metadata.get("content", ""),
                        "title": match.metadata.get("title", ""),
                        "metadata": match.metadata,
                    }
                )

            return documents

        except Exception as e:
            
            return []

    def delete_document(self, doc_id: str) -> bool:
        if not self._initialize():
            print(f"PineconeService not initialized: {self._initialization_error}")
            return False

        try:
            self.index.delete(ids=[doc_id])
            return True
        except Exception as e:
            
            return False

    def is_available(self) -> bool:
        return self._initialize()
