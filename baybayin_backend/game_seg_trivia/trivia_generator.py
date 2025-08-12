# baybayin_backend/game_seg_trivia/trivia_generator.py
import os
import sys

# Add the Django project root to Python path 
# The Django project root is the outer baybayin_backend directory
current_dir = os.path.dirname(os.path.abspath(__file__))  # game_seg_trivia dir
django_project_root = os.path.dirname(current_dir)  # outer baybayin_backend dir (Django project root)
sys.path.insert(0, django_project_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baybayin_backend.settings")
import django
django.setup()
import random
import requests
import os
import logging
import re
import json
import time
from json.decoder import JSONDecodeError
from game_seg_trivia.content_retrieval import retrieve_relevant_facts, get_adaptive_fact, get_random_fact
from game_seg_trivia.adaptive_initializer import get_user_profile, update_user_profile, update_mastery_level
from game_seg_trivia.models import UserTriviaProfile, TriviaQuestionHistory
from game_seg_trivia.game_config import XP_VALUES, BONUS_MULTIPLIERS, DIFFICULTY_WEIGHTS, QUESTION_TYPES
from django.contrib.auth.models import User

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# API keys and URLs from environment variables
CHUTES_API_KEY = os.environ.get("CHUTES_API_KEY", "cpk_777c5219f7c84941b988f3f4fe53f035.8a1a0fe7b47f52fa99accaba7cb18a75.QYPuhChmrwwkTlzZ7cwkJvIo9ftkI9Yu")
CHUTES_API_URL = os.environ.get("CHUTES_API_URL", "https://llm.chutes.ai/v1/chat/completions")

def extract_first_json_object(text):
    """Robust JSON extraction with multiple fallback methods"""
    # Try parsing the entire response as JSON first
    try:
        return json.loads(text)
    except JSONDecodeError:
        pass
    
    # Try finding JSON objects with regex
    json_matches = re.findall(r'\{[\s\S]*?\}', text)
    for match in json_matches:
        try:
            return json.loads(match)
        except JSONDecodeError:
            continue
    
    # Try bracket counting method
    brace_stack = []
    start = None
    for i, c in enumerate(text):
        if c == '{':
            if not brace_stack:
                start = i
            brace_stack.append(c)
        elif c == '}':
            if brace_stack:
                brace_stack.pop()
                if not brace_stack and start is not None:
                    json_str = text[start:i+1]
                    try:
                        return json.loads(json_str)
                    except Exception as e:
                        logger.error(f"Failed bracket parse: {e}")
    
    # Final try: extract between first { and last }
    try:
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return json.loads(text[start_idx:end_idx])
    except Exception as e:
        logger.error(f"Final extraction failed: {e}")
    
    logger.error(f"No valid JSON found in: {text[:300]}...")
    return None

def analyze_question_difficulty(question):
    """
    Categorize question difficulty based on content
    """
    question = question.lower()
    
    # Basic fact recall
    if any(term in question for term in ["what is", "define", "describe", "type of", "best describes"]):
        return "basic_fact"
    
    # Historical context
    if any(term in question for term in ["when", "historically", "origin", "pre-colonial", "century", "spanish", "colonization"]):
        return "historical_context"
    
    # Linguistic analysis
    if any(term in question for term in ["syllable", "consonant", "vowel", "diacritic", "transcribe", "character represents", "symbol for"]):
        return "linguistic_analysis"
    
    # Comparative analysis
    if any(term in question for term in ["compare", "different from", "similar to", "vs", "versus", "unlike", "like"]):
        return "comparative_analysis"
    
    return "basic_fact"

def generate_trivia_from_fact(fact):
    """Simple fallback trivia generator"""
    if hasattr(fact, 'summary'):
        context = fact.summary
    elif hasattr(fact, 'definition'):
        context = fact.definition
    else:
        context = str(fact)

    question = f"What is the following about?\n\n{context}"
    options = [
        getattr(fact, 'title', None) or getattr(fact, 'term', None) or "Baybayin",
        "Tagalog Script",
        "Ancient Filipino Writing",
        "Philippine Alphabet"
    ]
    random.shuffle(options)
    answer = getattr(fact, 'title', None) or getattr(fact, 'term', None) or "Baybayin"

    return {
        "question": question,
        "options": options,
        "answer": answer,
        "source_fact": fact.id if fact else None
    }

def build_rag_prompt(facts, recent_types=None):
    """
    Build RAG prompt with strict JSON instructions and diversity
    """
    context = "\n\n".join(
        getattr(f, 'summary', None) or getattr(f, 'definition', None) or str(f)
        for f in facts
    )
    
    prompt = f"""
Context:
{context}

Task:
Generate a multiple-choice trivia question about Baybayin based on the context above.

Important Requirements:
1. Avoid repeating the same question types (if recent types provided)
2. Focus on different aspects of Baybayin
3. Output ONLY valid JSON with no additional text
4. Use this exact format:
{{
  "question": "Your question here?",
  "options": ["Option1", "Option2", "Option3", "Option4"],
  "answer": "CorrectOption"
}}
5. Ensure:
   - "answer" exactly matches one option
   - Options are Baybayin-related
   - No markdown or code formatting
"""
    # Add recent types warning if available
    if recent_types:
        type_str = ", ".join(set(recent_types))
        prompt += f"\nRecent question types to avoid: {type_str}"
    
    return prompt

def generate_trivia_with_rag(query, user_profile=None, provider="deepseek", recent_types=None):
    """
    Retrieve relevant facts and generate trivia with RAG and diversity
    """
    # Get recent fact IDs to exclude
    exclude_ids = []
    if user_profile:
        # Get last 5 asked questions
        recent_questions = TriviaQuestionHistory.objects.filter(
            user=user_profile.user
        ).order_by('-timestamp')[:5]
        
        # Extract fact IDs
        for q in recent_questions:
            if q.source_fact:
                if isinstance(q.source_fact, list):
                    exclude_ids.extend(q.source_fact)
                else:
                    exclude_ids.append(q.source_fact)
    
    facts = retrieve_relevant_facts(query, user_profile, top_k=3, exclude_ids=exclude_ids)
    prompt = build_rag_prompt(facts, recent_types)
    
    headers = {
        "Authorization": f"Bearer {CHUTES_API_KEY}",
        "Content-Type": "application/json"
    }
    
    model = "deepseek-ai/DeepSeek-R1" if provider == "deepseek" else "gpt-3.5-turbo"
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 256,
        "temperature": 0.7,
        "response_format": {"type": "json_object"}  # Force JSON output
    }
    
    try:
        response = requests.post(CHUTES_API_URL, headers=headers, json=data)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        logger.info(f"RAG raw response: {content[:200]}...")
    except Exception as e:
        logger.error(f"{provider} API error: {e}")
        return {
            "question": "[LLM API error]", 
            "options": [], 
            "answer": "",
            "source_facts": [f.id for f in facts] if facts else None
        }

    trivia = extract_first_json_object(content)
    if trivia:
        trivia["source_facts"] = [f.id for f in facts] if facts else None
        return trivia
    else:
        logger.warning("RAG response did not contain valid JSON")
        return {
            "question": content, 
            "options": [], 
            "answer": "",
            "source_facts": [f.id for f in facts] if facts else None
        }

def calculate_points(user_profile, trivia, is_correct, answer_time, source_fact=None):
    """
    Calculate points earned for a question response
    """
    # Base values
    level_config = user_profile.level_config
    difficulty = level_config["difficulty"]
    base_xp = XP_VALUES[difficulty]["correct"] if is_correct else XP_VALUES[difficulty]["incorrect"]
    
    # Initialize multiplier
    multiplier = 1.0
    
    # Combo bonus (consecutive correct answers)
    if is_correct:
        user_profile.consecutive_correct += 1
        for threshold, bonus in BONUS_MULTIPLIERS["combo"].items():
            if user_profile.consecutive_correct >= threshold:
                multiplier *= bonus
    else:
        user_profile.consecutive_correct = 0
    
    # Time bonus (faster answers get bonus)
    if is_correct:  # Only reward quick correct answers
        for threshold, bonus in BONUS_MULTIPLIERS["time"].items():
            if answer_time <= threshold:
                multiplier *= bonus
                break
    
    # Weakness bonus (correct answer on weak topic)
    if is_correct and source_fact and user_profile.top_weaknesses:
        # Check if source fact relates to weak topics
        fact_topics = []
        if hasattr(source_fact, 'title'):
            fact_topics.append(source_fact.title)
        if hasattr(source_fact, 'term'):
            fact_topics.append(source_fact.term)
        if hasattr(source_fact, 'tags'):
            fact_topics.extend(source_fact.tags)
            
        if any(topic in user_profile.top_weaknesses for topic in fact_topics):
            multiplier *= BONUS_MULTIPLIERS["weakness"]
    
    # Mastery bonus
    multiplier *= BONUS_MULTIPLIERS["mastery"].get(user_profile.mastery_level, 1.0)
    
    # Question difficulty weighting
    question_type = analyze_question_difficulty(trivia['question'])
    multiplier *= DIFFICULTY_WEIGHTS.get(question_type, 1.0)
    
    # Calculate final points
    points = int(base_xp * multiplier)
    
    # Ensure minimum points
    if is_correct and points < 20:
        points = 20  # Minimum reward for correct answers
    
    return points

if __name__ == "__main__":
    # Create or get a default user for the terminal session
    user, _ = User.objects.get_or_create(username='terminal_user')
    user_profile = get_user_profile(user)
    
    # Initialize level if needed
    if user_profile.moves_remaining <= 0:
        user_profile.initialize_level()
    
    level_config = user_profile.level_config
    
    print(f"=== Level {user_profile.current_level} ===")
    print(f"Target XP: {level_config['target_xp']} | Moves left: {user_profile.moves_remaining}")
    print(f"Mastery Level: {user_profile.mastery_level}")
    
    # Get recent question types for diversity
    recent_types = TriviaQuestionHistory.objects.filter(
        user=user_profile.user
    ).order_by('-timestamp').values_list('question_type', flat=True)[:3]
    
    while user_profile.moves_remaining > 0:
        retries = 0
        trivia = None
        source_fact = None

        # Try generating valid trivia
        while retries < 3:
            try:
                # Use adaptive learning: 30% chance to focus on weak areas
                if user_profile.top_weaknesses and random.random() < 0.3:
                    source_fact = get_adaptive_fact(user_profile)
                    trivia = generate_trivia_from_fact(source_fact)
                else:
                    # Use RAG for broader context with diversity
                    trivia = generate_trivia_with_rag(
                        "Baybayin", 
                        user_profile, 
                        provider="deepseek",
                        recent_types=recent_types
                    )
                    source_fact = trivia.get("source_facts")
                
                # Validate the trivia structure
                if (trivia.get("question") and 
                    isinstance(trivia.get("options"), list) and 
                    len(trivia["options"]) >= 2 and 
                    trivia.get("answer")):
                    break
                
                logger.warning(f"Invalid trivia format. Retrying... ({retries + 1}/3)")
            except Exception as e:
                logger.error(f"Trivia generation error: {e}")
            
            retries += 1

        # Fallback to simple generator if RAG fails
        if not trivia or not trivia.get("question") or not trivia.get("options"):
            logger.warning("Using fallback trivia generator")
            source_fact = get_adaptive_fact(user_profile) or get_random_fact()
            trivia = generate_trivia_from_fact(source_fact)

        print(f"\nTrivia Question {user_profile.session_moves + 1}:")
        print(trivia["question"])
        print("Options:")
        for idx, opt in enumerate(trivia["options"], 1):
            print(f"{idx}. {opt}")

        start_time = time.time()
        user_choice = input("\nYour answer (type the number or text, 'quit' to exit): ").strip()
        
        if user_choice.lower() == "quit":
            print("Thanks for playing!")
            break
        
        # Check answer by index or text
        try:
            choice_index = int(user_choice) - 1
            if 0 <= choice_index < len(trivia["options"]):
                user_answer = trivia["options"][choice_index]
            else:
                user_answer = user_choice
        except ValueError:
            user_answer = user_choice

        # Calculate time taken
        answer_time = time.time() - start_time
        
        # Determine if correct
        is_correct = user_answer.lower() == trivia.get("answer", "").lower()
        
        # Calculate points
        points = calculate_points(
            user_profile=user_profile,
            trivia=trivia,
            is_correct=is_correct,
            answer_time=answer_time,
            source_fact=source_fact
        )
        
        # Update user profile with performance data
        question_type = analyze_question_difficulty(trivia['question'])
        update_user_profile(
            user=user,
            question=trivia,
            user_answer=user_answer,
            correct_answer=trivia.get('answer', ''),
            source_fact=source_fact,
            question_type=question_type
        )
        
        # Update XP and moves
        user_profile.current_xp += points
        if is_correct:
            print(f"✅ Correct! +{points} XP")
        else:
            print(f"❌ Incorrect! {points} XP")
        
        user_profile.moves_remaining -= 1
        user_profile.session_moves += 1
        user_profile.save()
        
        # Update mastery based on performance
        update_mastery_level(user_profile)
        
        # Show progress
        print(f"Level Progress: {user_profile.current_xp}/{level_config['target_xp']} "
              f"({user_profile.level_progress}%)")
        print(f"Moves remaining: {user_profile.moves_remaining}")
        
        # Update recent types for next question
        recent_types = [question_type] + list(recent_types)[:2]
        
        # Check level completion
        if user_profile.current_xp >= level_config['target_xp']:
            print("\n🌟 Level Completed! 🌟")
            user_profile.complete_level()
            print(f"Advancing to Level {user_profile.current_level}!")
            break
            
        # Check level failure
        if user_profile.moves_remaining <= 0:
            print("\n💥 Level Failed! 💥")
            print(f"You earned {user_profile.current_xp} XP, "
                  f"needed {level_config['target_xp']}")
            user_profile.fail_level()
            break