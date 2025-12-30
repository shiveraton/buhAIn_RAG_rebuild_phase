#!/usr/bin/env python
"""
Simple test script for AI-driven trivia endpoints
"""
import os
import sys
import django
import requests
import json
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baybayin_backend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialize Django
django.setup()

# Now we can import Django models
from game_seg_trivia.models import UserSkillProfile, TriviaQuestionAnswered
from baybayin_codex_pdf.models import PDFCodexEntry
from django.contrib.auth.models import User

def test_ai_content_analysis():
    """Test if AI content analysis populated the data correctly"""
    print("🔍 Testing AI Content Analysis Results...")
    
    # Check if we have analyzed PDF entries
    analyzed_entries = PDFCodexEntry.objects.exclude(ai_difficulty_score__isnull=True)
    print(f"   • Found {analyzed_entries.count()} AI-analyzed PDF entries")
    
    if analyzed_entries.exists():
        sample = analyzed_entries.first()
        print(f"   • Sample entry: difficulty={sample.ai_difficulty_score}, category={sample.ai_category}")
        return True
    else:
        print("   ❌ No AI-analyzed entries found")
        return False

def test_models_creation():
    """Test if our new models work correctly"""
    print("🧪 Testing Model Creation...")
    
    try:
        # Create test user
        user, created = User.objects.get_or_create(
            username='test_ai_user',
            defaults={'email': 'test@example.com'}
        )
        print(f"   • User: {'created' if created else 'exists'}")
        
        # Create UserSkillProfile
        profile, created = UserSkillProfile.objects.get_or_create(
            user=user,
            defaults={
                'overall_skill': 1000.0,
                'skill_uncertainty': 350.0,
                'learning_rate': 1.0
            }
        )
        print(f"   • UserSkillProfile: {'created' if created else 'exists'}")
        print(f"   • Profile data: skill={profile.overall_skill}, uncertainty={profile.skill_uncertainty}")
        
        return True
    except Exception as e:
        print(f"   ❌ Model creation failed: {e}")
        return False

def test_adaptive_question_selector():
    """Test the adaptive question selector logic"""
    print("🎯 Testing Adaptive Question Selector...")
    
    try:
        from game_seg_trivia.adaptive_question_selector import AdaptiveQuestionSelector
        
        # Create a test user if not exists
        user, _ = User.objects.get_or_create(
            username='test_selector_user',
            defaults={'email': 'test2@example.com'}
        )
        
        # Get or create user skill profile
        profile, _ = UserSkillProfile.objects.get_or_create(
            user=user,
            defaults={'overall_skill': 1000.0}
        )
        
        # Test content selection
        content = AdaptiveQuestionSelector.select_next_question(profile)
        print(f"   • Selected content: {bool(content)}")
        
        if content:
            print(f"   • Selected content: ID={content.id}, difficulty={content.ai_difficulty_score}")
        
        return bool(content)
    except Exception as e:
        print(f"   ❌ Selector test failed: {e}")
        return False

def test_trivia_generation():
    """Test trivia question generation"""
    print("🎮 Testing Trivia Generation...")
    
    try:
        from game_seg_trivia.trivia_generator import generate_trivia_from_fact
        
        # Get a sample PDF entry
        entry = PDFCodexEntry.objects.first()
        if not entry:
            print("   ❌ No PDF entries found")
            return False
        
        # Generate trivia
        trivia_data = generate_trivia_from_fact(entry.text)
        print(f"   • Generated trivia: {bool(trivia_data)}")
        
        if trivia_data:
            print(f"   • Question preview: {trivia_data.get('question', 'N/A')[:50]}...")
        
        return bool(trivia_data)
    except Exception as e:
        print(f"   ❌ Trivia generation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 AI-Driven Trivia System Test Suite")
    print("=" * 50)
    
    tests = [
        ("AI Content Analysis", test_ai_content_analysis),
        ("Model Creation", test_models_creation),
        ("Adaptive Selector", test_adaptive_question_selector),
        ("Trivia Generation", test_trivia_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append(result)
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   Result: {status}")
        except Exception as e:
            print(f"   Result: ❌ ERROR - {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   • Passed: {sum(results)}/{len(results)}")
    print(f"   • Success Rate: {sum(results)/len(results)*100:.1f}%")
    
    if all(results):
        print("🎉 All tests passed! Your AI trivia system is ready!")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()
