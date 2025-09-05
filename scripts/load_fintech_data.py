Script to load fintech FAQs into the vector database.
This script processes the fintech_faqs.json file and stores each FAQ
as a vector embedding in Pinecone for RAG functionality.

import json
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from services.pinecone_service import PineconeService
from config import settings

def load_fintech_faqs():

    pinecone_service = PineconeService()

    if not pinecone_service.is_available():
        print(
            "❌ PineconeService is not available. Please check your API keys and configuration."
        )
        print("Make sure you have:")
        print("1. Valid PINECONE_API_KEY")
        print("2. Valid OPENAI_API_KEY")
        print("3. Correct PINECONE_INDEX_NAME")
        return False

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

    successful_uploads = 0
    failed_uploads = 0

    for i, faq in enumerate(faqs, 1):
        try:
            content = f"""
Question: {faq['question']}

Answer: {faq['answer']}

Keywords: {', '.join(faq['keywords'])}

            metadata = {
                "category": faq["category"],
                "question": faq["question"],
                "answer": faq["answer"],
                "keywords": faq["keywords"],
                "faq_type": "fintech",
                "source": "fintech_faqs.json",
            }

            doc_id = pinecone_service.store_document(
                content=content, title=f"FAQ: {faq['question']}", metadata=metadata
            )

            print(
                f"✅ [{i:2d}/{len(faqs)}] Stored FAQ: {faq['question'][:60]}... (ID: {doc_id[:8]}...)"
            )
            successful_uploads += 1

        except Exception as e:
            print(
                f"❌ [{i:2d}/{len(faqs)}] Failed to store FAQ: {faq['question'][:60]}... Error: {e}"
            )
            failed_uploads += 1

    print("\n" + "=" * 60)
    print("📊 UPLOAD SUMMARY")
    print("=" * 60)
    print(f"✅ Successful uploads: {successful_uploads}")
    print(f"❌ Failed uploads: {failed_uploads}")
    print(f"📋 Total FAQs: {len(faqs)}")
    print(f"📈 Success rate: {(successful_uploads/len(faqs)*100):.1f}%")

    if successful_uploads > 0:
        print(
            "\n🎉 Fintech FAQs have been successfully loaded into the vector database!"
        )
        print("🤖 Your chatbot is now ready to answer fintech-related questions.")

        print("\n💡 Try asking questions like:")
        print("  • 'How do I create a new account?'")
        print("  • 'What are your transaction limits?'")
        print("  • 'How do you protect my account from fraud?'")
        print("  • 'Are you FDIC insured?'")
        print("  • 'Why was my transaction declined?'")

    return successful_uploads > 0

def main():
    print("🚀 Fintech FAQ Data Loader")
    print("=" * 50)

    print("🔍 Checking environment configuration...")

    if (
        not settings.pinecone_api_key
        or settings.pinecone_api_key == "your-pinecone-api-key-here"
    ):
        print(
            "❌ Pinecone API key not configured. Please set PINECONE_API_KEY in your .env file."
        )
        return 1

    if (
        not settings.openai_api_key
        or settings.openai_api_key == "sk-your-openai-api-key-here"
    ):
        print(
            "❌ OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file."
        )
        return 1

    print("✅ Environment configuration looks good!")
    print()

    success = load_fintech_faqs()

    if success:
        print("\n🎯 Next steps:")
        print("1. Start your API server: python3 main.py")
        print(
            "2. Test the chatbot with fintech questions using your Insomnia collection"
        )
        print("3. The chatbot will now use RAG to provide accurate fintech answers!")
        return 0
    else:
        print("\n❌ Data loading failed. Please check the errors above and try again.")
        return 1

if __name__ == "__main__":
    exit(main())
