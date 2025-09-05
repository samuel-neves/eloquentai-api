#!/usr/bin/env python3
"""
Test script for the fintech chatbot functionality.
This script tests the complete flow: data loading, authentication, and chatbot responses.
"""

import requests
import json
import time
from pathlib import Path


class FintechChatbotTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_token = None
        self.session_id = None

    def test_api_health(self):
        """Test API health endpoints"""
        print("🔍 Testing API health...")

        try:
            # Test root endpoint
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                print("✅ Root endpoint working")
                print(f"   Version: {response.json().get('version', 'Unknown')}")
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                return False

            # Test global health
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ Global health check working")
            else:
                print(f"❌ Global health check failed: {response.status_code}")
                return False

            # Test chat health
            response = requests.get(f"{self.base_url}/api/chat/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Chat health: {health_data.get('status', 'unknown')}")
                print(f"   Message: {health_data.get('message', 'N/A')}")
            else:
                print(f"❌ Chat health check failed: {response.status_code}")
                return False

            return True

        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to API. Make sure the server is running.")
            return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

    def test_authentication(self):
        """Test authentication system"""
        print("\n🔐 Testing authentication...")

        try:
            # Test demo credentials endpoint
            response = requests.get(f"{self.base_url}/api/auth/demo-credentials")
            if response.status_code == 200:
                print("✅ Demo credentials endpoint working")

            # Test anonymous session creation
            response = requests.post(f"{self.base_url}/api/auth/anonymous")
            if response.status_code == 200:
                auth_data = response.json()
                self.session_token = auth_data["token"]
                self.session_id = auth_data["session_id"]
                print("✅ Anonymous session created")
                print(f"   Session ID: {self.session_id[:8]}...")
                print(f"   User type: {auth_data['user_type']}")
            else:
                print(f"❌ Anonymous session creation failed: {response.status_code}")
                return False

            # Test authenticated login
            login_data = {"email": "demo@fintech.com", "password": "demo123"}
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                print("✅ Authenticated login working")
                auth_data = response.json()
                print(f"   User type: {auth_data['user_type']}")
            else:
                print(f"❌ Authenticated login failed: {response.status_code}")

            return True

        except Exception as e:
            print(f"❌ Authentication test error: {e}")
            return False

    def test_fintech_categories(self):
        """Test fintech category endpoints"""
        print("\n📋 Testing fintech categories...")

        try:
            # Test categories list
            response = requests.get(f"{self.base_url}/api/fintech/categories")
            if response.status_code == 200:
                categories_data = response.json()
                print("✅ Categories endpoint working")
                print(f"   Total categories: {categories_data['total_categories']}")
                for category in categories_data["categories"]:
                    print(f"   - {category['name']}")
            else:
                print(f"❌ Categories endpoint failed: {response.status_code}")
                return False

            return True

        except Exception as e:
            print(f"❌ Categories test error: {e}")
            return False

    def test_chatbot_responses(self):
        """Test chatbot with fintech questions"""
        print("\n🤖 Testing chatbot responses...")

        # Test questions for each category
        test_questions = [
            ("How do I create a new account?", "Account & Registration"),
            ("What are your transaction limits?", "Payments & Transactions"),
            (
                "How do you protect my account from fraud?",
                "Security & Fraud Prevention",
            ),
            ("Are you FDIC insured?", "Regulations & Compliance"),
            ("The app is not working properly", "Technical Support & Troubleshooting"),
        ]

        headers = {}
        if self.session_token:
            headers["Authorization"] = f"Bearer {self.session_token}"

        successful_responses = 0

        for question, expected_category in test_questions:
            try:
                print(f"\n📝 Testing: {question}")

                # Test regular chat endpoint
                chat_data = {"message": question, "conversation_id": None}
                response = requests.post(
                    f"{self.base_url}/api/chat/message", json=chat_data, headers=headers
                )

                if response.status_code == 200:
                    chat_result = response.json()
                    print("✅ Chat response received")
                    print(f"   Sources found: {len(chat_result.get('sources', []))}")
                    print(f"   Response length: {len(chat_result.get('response', ''))}")

                    # Show first part of response
                    response_text = chat_result.get("response", "")
                    preview = (
                        response_text[:150] + "..."
                        if len(response_text) > 150
                        else response_text
                    )
                    print(f"   Preview: {preview}")

                    successful_responses += 1
                else:
                    print(f"❌ Chat failed: {response.status_code}")
                    print(f"   Error: {response.text}")

                # Test category-specific endpoint
                category_data = {"question": question, "category": expected_category}
                response = requests.post(
                    f"{self.base_url}/api/fintech/ask-by-category",
                    json=category_data,
                    headers=headers,
                )

                if response.status_code == 200:
                    category_result = response.json()
                    print(
                        f"✅ Category response: confidence {category_result.get('confidence_score', 0):.2f}"
                    )
                    if category_result.get("related_categories"):
                        print(
                            f"   Related: {', '.join(category_result['related_categories'])}"
                        )
                else:
                    print(f"❌ Category query failed: {response.status_code}")

                time.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"❌ Error testing question '{question}': {e}")

        print(
            f"\n📊 Chat test summary: {successful_responses}/{len(test_questions)} successful"
        )
        return successful_responses == len(test_questions)

    def test_document_search(self):
        """Test document search functionality"""
        print("\n🔍 Testing document search...")

        try:
            # Test search endpoint
            search_params = {"query": "account verification", "top_k": 3}
            response = requests.get(
                f"{self.base_url}/api/documents/search", params=search_params
            )

            if response.status_code == 200:
                search_results = response.json()
                print("✅ Document search working")
                print(f"   Results found: {search_results.get('count', 0)}")

                # Show sample results
                for i, result in enumerate(search_results.get("results", [])[:2]):
                    print(f"   [{i+1}] Score: {result.get('score', 0):.3f}")
                    print(f"       Title: {result.get('title', 'N/A')[:60]}...")
            else:
                print(f"❌ Document search failed: {response.status_code}")
                return False

            return True

        except Exception as e:
            print(f"❌ Document search error: {e}")
            return False

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting Fintech Chatbot Test Suite")
        print("=" * 50)

        tests_passed = 0
        total_tests = 5

        # Run all tests
        if self.test_api_health():
            tests_passed += 1

        if self.test_authentication():
            tests_passed += 1

        if self.test_fintech_categories():
            tests_passed += 1

        if self.test_chatbot_responses():
            tests_passed += 1

        if self.test_document_search():
            tests_passed += 1

        # Summary
        print("\n" + "=" * 50)
        print("🎯 TEST SUMMARY")
        print("=" * 50)
        print(f"Tests passed: {tests_passed}/{total_tests}")
        print(f"Success rate: {(tests_passed/total_tests*100):.1f}%")

        if tests_passed == total_tests:
            print("\n🎉 ALL TESTS PASSED! Your fintech chatbot is working perfectly!")
            print("\n💡 Next steps:")
            print("1. Load your fintech FAQ data: python3 scripts/load_fintech_data.py")
            print("2. Import the Insomnia collection for manual testing")
            print("3. Test with real users!")
        else:
            print(
                f"\n⚠️  {total_tests - tests_passed} tests failed. Check the errors above."
            )

        return tests_passed == total_tests


def main():
    """Main function"""
    import sys

    # Allow custom base URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    print(f"Testing API at: {base_url}")

    tester = FintechChatbotTester(base_url)
    success = tester.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
