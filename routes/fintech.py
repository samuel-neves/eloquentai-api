from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from services.chat_service import ChatService
from services.auth_service import AuthService
from routes.auth import get_session_from_header

router = APIRouter(prefix="/fintech", tags=["fintech"])
chat_service = ChatService()
auth_service = AuthService()

class CategoryQuery(BaseModel):
    question: str
    category: str
    session_id: Optional[str] = None

class CategoryResponse(BaseModel):
    answer: str
    category: str
    confidence_score: float
    sources: List[str]
    related_categories: List[str]
    session_id: str

class CategoryListResponse(BaseModel):
    categories: List[Dict[str, str]]
    total_categories: int

@router.get("/categories", response_model=CategoryListResponse)
async def get_fintech_categories() -> CategoryListResponse:
    categories = [
        {
            "name": "Account & Registration",
            "description": "Questions about creating accounts, verification, and profile management",
        },
        {
            "name": "Payments & Transactions",
            "description": "Questions about transfers, limits, fees, and transaction processing",
        },
        {
            "name": "Security & Fraud Prevention",
            "description": "Questions about account security, fraud protection, and safety measures",
        },
        {
            "name": "Regulations & Compliance",
            "description": "Questions about FDIC insurance, regulations, and compliance requirements",
        },
        {
            "name": "Technical Support & Troubleshooting",
            "description": "Questions about app issues, login problems, and technical assistance",
        },
    ]

    return CategoryListResponse(categories=categories, total_categories=len(categories))

@router.post("/ask-by-category", response_model=CategoryResponse)
async def ask_by_category(
    request: CategoryQuery,
    session: Optional[Dict[str, Any]] = Depends(get_session_from_header),
) -> CategoryResponse:
    if not session:
        session_id = auth_service.create_session()
        session = auth_service.get_session(session_id)
    else:
        session_id = session["session_id"]

    valid_categories = chat_service.get_fintech_categories()
    if request.category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Valid categories: {', '.join(valid_categories)}",
        )

    try:
        enhanced_query = f"[Category: {request.category}] {request.question}"

        result = chat_service.generate_response(
            message=enhanced_query, conversation_id=session_id
        )

        auth_service.update_session_activity(
            session_id, {"category_query": request.category, "new_conversation": True}
        )

        confidence_score = calculate_confidence_score(
            result["sources"], request.category
        )

        related_categories = find_related_categories(
            request.category, result["sources"]
        )

        return CategoryResponse(
            answer=result["response"],
            category=request.category,
            confidence_score=confidence_score,
            sources=result["sources"],
            related_categories=related_categories,
            session_id=result["conversation_id"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing category query: {str(e)}"
        )

@router.get("/search-by-category/{category}")
async def search_by_category(
    category: str, query: str, limit: int = 5
) -> Dict[str, Any]:
    valid_categories = chat_service.get_fintech_categories()
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Valid categories: {', '.join(valid_categories)}",
        )

    try:
        enhanced_query = f"Category: {category} - {query}"

        rag_result = chat_service.retrieve_relevant_context(enhanced_query, top_k=limit)

        filtered_sources = []
        for source in rag_result["sources"]:
            if category.lower() in source.lower():
                filtered_sources.append(source)

        return {
            "category": category,
            "query": query,
            "results": filtered_sources[:limit],
            "total_found": len(filtered_sources),
            "context_categories": rag_result["categories"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error searching category: {str(e)}"
        )

@router.get("/category-stats/{category}")
async def get_category_stats(category: str) -> Dict[str, Any]:
    valid_categories = chat_service.get_fintech_categories()
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Valid categories: {', '.join(valid_categories)}",
        )

    try:
        rag_result = chat_service.retrieve_relevant_context(
            f"Category: {category}", top_k=50
        )

        category_faqs = [
            source
            for source in rag_result["sources"]
            if category.lower() in source.lower()
        ]

        return {
            "category": category,
            "total_faqs": len(category_faqs),
            "sample_questions": category_faqs[:5],
            "related_categories": rag_result["categories"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting category stats: {str(e)}"
        )

def calculate_confidence_score(sources: List[str], category: str) -> float:
    if not sources:
        return 0.0

    category_matches = sum(
        1 for source in sources if category.lower() in source.lower()
    )
    base_score = category_matches / len(sources)

    if len(sources) >= 3 and category_matches >= 2:
        base_score += 0.1

    return min(base_score, 1.0)

def find_related_categories(current_category: str, sources: List[str]) -> List[str]:
    all_categories = [
        "Account & Registration",
        "Payments & Transactions",
        "Security & Fraud Prevention",
        "Regulations & Compliance",
        "Technical Support & Troubleshooting",
    ]

    related = []
    for category in all_categories:
        if category != current_category:
            if any(category.lower() in source.lower() for source in sources):
                related.append(category)

    return related[:3]
