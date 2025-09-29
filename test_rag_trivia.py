#!/usr/bin/env python3
"""
Test script to verify RAG-powered trivia generation
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/trivia"

def test_rag_trivia():
    """Test the RAG-powered trivia generation"""
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    print("🤖 Testing RAG-powered trivia generation...")
    print("="*50)
    
    for i in range(3):  # Test 3 questions to see variety
        print(f"\n📝 Test {i+1}: Getting RAG-generated question...")
        
        # Get a question
        question_response = session.get(f"{BASE_URL}/question/")
        print(f"Status: {question_response.status_code}")
        
        if question_response.status_code == 200:
            question_data = question_response.json()
            question_text = question_data.get('trivia', {}).get('question', 'No question')
            options = question_data.get('trivia', {}).get('options', [])
            
            print(f"🎯 Question: {question_text}")
            print(f"📋 Options: {options}")
            
            # Check if this looks like a RAG-generated question (not static)
            static_questions = [
                'What does the Baybayin script "ᜊ" represent?',
                'What does the Baybayin script "ᜃ" represent?',
                'What does the Baybayin script "ᜄ" represent?',
                'What does the Baybayin script "ᜋ" represent?'
            ]
            
            if question_text in static_questions:
                print("⚠️  This appears to be a static fallback question")
            else:
                print("✅ This appears to be a RAG-generated dynamic question!")
            
            # Try to answer with the first option (for testing)
            if options:
                test_answer = options[0]
                print(f"🔄 Testing answer: '{test_answer}'...")
                
                answer_data = {"user_answer": test_answer}
                submit_response = session.post(f"{BASE_URL}/submit-answer/", 
                                            json=answer_data,
                                            headers={'Content-Type': 'application/json'})
                
                if submit_response.status_code == 200:
                    result_data = submit_response.json()
                    print(f"✅ Result: {result_data.get('result')}")
                    print(f"🎯 Correct answer was: {result_data.get('correct_answer')}")
                    print(f"⭐ Points: {result_data.get('points')}")
                else:
                    print(f"❌ Submit failed: {submit_response.text}")
            
            print("-" * 30)
            time.sleep(2)  # Small delay between questions
            
        else:
            print(f"❌ Question failed: {question_response.text}")
            break
    
    print(f"\n🎉 RAG trivia test completed!")

if __name__ == "__main__":
    test_rag_trivia()
