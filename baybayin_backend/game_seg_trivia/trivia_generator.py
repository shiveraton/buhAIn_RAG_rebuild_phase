import os
import random
import logging
import json
import re
import requests
import numpy as np

from game_seg_trivia.content_retrieval import retrieve_relevant_facts, get_adaptive_fact, get_random_fact
from game_seg_trivia.adaptive_initializer import get_user_profile, update_user_profile, update_mastery_level
from game_seg_trivia.models import UserTriviaProfile, TriviaQuestionHistory
from game_seg_trivia.game_config import XP_VALUES, BONUS_MULTIPLIERS, DIFFICULTY_WEIGHTS
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# API Config
CHUTES_API_KEY = os.environ.get("CHUTES_API_KEY")
CHUTES_API_URL = os.environ.get("CHUTES_API_URL", "https://llm.chutes.ai/v1/chat/completions")


# ---------------------------
# Fact Validation Utilities
# ---------------------------
def validate_fact_text(text, fact_id=None, fact_type=None):
    """Validate fact text to filter out OCR garbage or broken characters."""
    if not text or not isinstance(text, str) or len(text) < 40:
        logger.warning(f"Rejected fact {fact_id} ({fact_type}): too short or non-string")
        return False

    alpha_ratio = sum(c.isalpha() for c in text) / len(text)
    if alpha_ratio < 0.5:
        logger.warning(f"Rejected fact {fact_id} ({fact_type}): too many non-alpha chars ({alpha_ratio:.2%})")
        return False

    return True


def extract_first_json_object(text):
    """Robust JSON extraction from LLM response."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    json_matches = re.findall(r'\{[\s\S]*?\}', text)
    for match in json_matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    # Fallback: first { to last }
    start_idx = text.find('{')
    end_idx = text.rfind('}') + 1
    if start_idx != -1 and end_idx != -1:
        try:
            return json.loads(text[start_idx:end_idx])
        except Exception:
            pass
    logger.error(f"No valid JSON extracted from LLM response: {text[:200]}...")
    return None


# ---------------------------
# RAG Prompt Builder
# ---------------------------
def build_rag_prompt(facts, recent_types=None, recent_answers=None):
    """Build prompt for LLM with facts and avoidance of recent questions/answers."""
    valid_facts = [
        f for f in facts
        if validate_fact_text(getattr(f, "text", getattr(f, "summary", getattr(f, "definition", ""))),
                              fact_id=getattr(f, "id", "unknown"),
                              fact_type=type(f).__name__)
    ]
    if not valid_facts:
        logger.warning("All facts filtered; using unfiltered facts as fallback.")
        valid_facts = facts

    context = "\n\n".join(
        getattr(f, "summary", getattr(f, "definition", getattr(f, "text", str(f))))
        for f in valid_facts
    )

    recent_types_str = ", ".join(set(recent_types)) if recent_types else "None"
    recent_answers_str = ", ".join(set(recent_answers)) if recent_answers else "None"

    prompt = f"""
You are a trivia writer who creates accurate multiple-choice questions about Baybayin.
ONLY use the information given in the Context. Do NOT invent or assume anything.

Context:
{context}

Recent question types to avoid: {recent_types_str}
Recent answers to avoid: {recent_answers_str}

Instructions:
1. Identify a clear, factual point from the context.
2. Generate ONE multiple-choice question about it.
3. Provide four options, including one correct answer.
4. The question must be precise, direct, and context-relevant.
5. Output JSON ONLY in this format:

{{
  "question": "Your question here?",
  "options": ["Option1", "Option2", "Option3", "Option4"],
  "answer": "CorrectOption"
}}

Example:
{{
  "question": "Which Baybayin character represents the syllable 'ba'?",
  "options": ["ᜊ", "ᜃ", "ᜇ", "ᜀ"],
  "answer": "ᜊ"
}}
"""
    return prompt

# ---------------------------
# Question Difficulty
# ---------------------------
def analyze_question_difficulty(question):
    """Categorize question difficulty for scoring."""
    q = question.lower()
    if any(term in q for term in ["what is", "define", "describe", "type of"]):
        return "basic_fact"
    if any(term in q for term in ["when", "historically", "origin", "century", "spanish", "colonization"]):
        return "historical_context"
    if any(term in q for term in ["syllable", "consonant", "vowel", "diacritic", "transcribe", "character represents"]):
        return "linguistic_analysis"
    if any(term in q for term in ["compare", "different from", "similar to", "vs", "versus"]):
        return "comparative_analysis"
    return "basic_fact"


# ---------------------------
# Trivia Generators
# ---------------------------
def generate_trivia_from_fact(fact):
    """Use PDF content directly as trivia question with dynamic options."""
    # Get the content directly from the PDF - this should already be a question
    context = getattr(fact, "text", getattr(fact, "summary", getattr(fact, "definition", str(fact))))
    
    # Clean up the content and use it directly as the question
    question = context.strip()
    
    # If the content doesn't end with a question mark, add one for clarity
    if question and not question.endswith('?'):
        question += '?'
    
    # Generate contextual options based on question content
    options, answer = generate_contextual_options(question, fact)
    
    return {"question": question, "options": options, "answer": answer, "source_fact": getattr(fact, "id", None)}


def generate_contextual_options(question, fact):
    """Generate realistic options based on question context and type."""
    
    question_lower = question.lower()
    
    # Baybayin character questions
    if any(char in question for char in ['ᜊ', 'ᜋ', 'ᜌ', 'ᜍ', 'ᜎ', 'ᜏ', 'ᜐ', 'ᜑ', 'ᜈ', 'ᜅ', 'ᜆ', 'ᜇ', 'ᜄ', 'ᜉ']):
        return generate_character_options(question, fact)
    
    # Sound/pronunciation questions
    elif any(word in question_lower for word in ['sound', 'pronounce', 'represents', 'tunog']):
        sounds = ['Ba', 'Ma', 'Ka', 'Sa', 'Ta', 'Na', 'Ga', 'Pa', 'La', 'Wa', 'Ya', 'Ra', 'Ha']
        correct_answer = extract_answer_from_context(question, fact) or random.choice(sounds)
        wrong_answers = [s for s in sounds if s != correct_answer]
        random.shuffle(wrong_answers)
        options = [correct_answer] + wrong_answers[:3]
        random.shuffle(options)
        return options, correct_answer
    
    # Historical questions
    elif any(word in question_lower for word in ['history', 'historical', 'spanish', 'colonial', 'century', 'period']):
        if 'century' in question_lower:
            historical_options = ['15th century', '16th century', '17th century', '18th century']
        else:
            historical_options = ['Pre-colonial period', 'Spanish colonial period', 'American period', 'Modern period']
        
        correct_answer = extract_answer_from_context(question, fact) or historical_options[0]
        wrong_answers = [opt for opt in historical_options if opt != correct_answer]
        random.shuffle(wrong_answers)
        options = [correct_answer] + wrong_answers[:3]
        random.shuffle(options)
        return options, correct_answer
    
    # Meaning/translation questions
    elif any(word in question_lower for word in ['mean', 'meaning', 'translate', 'kahulugan']):
        meanings = ['House', 'Tree', 'Water', 'Fire', 'Mountain', 'River', 'Sun', 'Moon', 'Love', 'Peace']
        correct_answer = extract_answer_from_context(question, fact) or random.choice(meanings)
        wrong_answers = [m for m in meanings if m != correct_answer]
        random.shuffle(wrong_answers)
        options = [correct_answer] + wrong_answers[:3]
        random.shuffle(options)
        return options, correct_answer
    
    # Kudlit/vowel questions
    elif any(word in question_lower for word in ['kudlit', 'vowel', 'diacritic', 'marker']):
        vowel_options = ['Above the character', 'Below the character', 'To the right', 'To the left']
        correct_answer = extract_answer_from_context(question, fact) or vowel_options[0]
        wrong_answers = [opt for opt in vowel_options if opt != correct_answer]
        random.shuffle(wrong_answers)
        options = [correct_answer] + wrong_answers[:3]
        random.shuffle(options)
        return options, correct_answer
    
    # Script type questions
    elif any(word in question_lower for word in ['type', 'classification', 'abugida', 'syllabic', 'script']):
        script_options = ['Abugida', 'Alphabet', 'Syllabary', 'Logographic']
        correct_answer = extract_answer_from_context(question, fact) or 'Abugida'
        wrong_answers = [opt for opt in script_options if opt != correct_answer]
        random.shuffle(wrong_answers)
        options = [correct_answer] + wrong_answers[:3]
        random.shuffle(options)
        return options, correct_answer
    
    # Default educational options
    else:
        generic_options = ['Syllabic writing system', 'Alphabetic system', 'Pre-colonial origin', 'Religious purposes']
        correct_answer = extract_answer_from_context(question, fact) or generic_options[0]
        wrong_answers = [opt for opt in generic_options if opt != correct_answer]
        random.shuffle(wrong_answers)
        options = [correct_answer] + wrong_answers[:3]
        random.shuffle(options)
        return options, correct_answer


def generate_character_options(question, fact):
    """Generate options for Baybayin character questions."""
    
    baybayin_chars = {
        'ᜊ': 'Ba', 'ᜋ': 'Ma', 'ᜌ': 'Ya', 'ᜍ': 'Ra', 'ᜎ': 'La', 'ᜏ': 'Wa',
        'ᜐ': 'Sa', 'ᜑ': 'Ha', 'ᜈ': 'Na', 'ᜅ': 'Nga', 'ᜆ': 'Ta', 'ᜇ': 'Ka',
        'ᜄ': 'Ga', 'ᜉ': 'Pa', 'ᜀ': 'A', 'ᜁ': 'I', 'ᜂ': 'U'
    }
    
    # Find the character in the question
    correct_answer = None
    for char, sound in baybayin_chars.items():
        if char in question:
            correct_answer = sound
            break
    
    # Fallback to context extraction or random
    if not correct_answer:
        correct_answer = extract_answer_from_context(question, fact) or random.choice(list(baybayin_chars.values()))
    
    # Generate wrong answers
    all_sounds = list(baybayin_chars.values())
    wrong_answers = [sound for sound in all_sounds if sound != correct_answer]
    random.shuffle(wrong_answers)
    
    options = [correct_answer] + wrong_answers[:3]
    random.shuffle(options)
    
    return options, correct_answer


def extract_answer_from_context(question, fact):
    """Try to extract the correct answer from the question or fact context."""
    
    context = getattr(fact, "text", getattr(fact, "summary", getattr(fact, "definition", "")))
    
    # Look for common answer patterns
    answer_patterns = [
        r'answer is ([^.]+)',
        r'correct answer: ([^.]+)',
        r'represents? ([^.]+)',
        r'means? ([^.]+)',
        r'refers to ([^.]+)'
    ]
    
    for pattern in answer_patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # Extract quoted text
    quoted = re.findall(r'"([^"]+)"', question)
    if quoted:
        return quoted[0]
    
    # Extract text after "is" or "are"
    is_match = re.search(r'\bis\s+([^?]+)', question, re.IGNORECASE)
    if is_match:
        return is_match.group(1).strip()
    
    return None


def generate_trivia_with_rag(query, user_profile=None, provider="deepseek", recent_types=None, recent_answers=None):
    """Generate trivia using RAG with recent questions tracking."""
    exclude_ids = []
    if user_profile:
        recent_questions = TriviaQuestionHistory.objects.filter(user=user_profile.user).order_by('-timestamp')[:5]
        for q in recent_questions:
            if q.source_fact:
                exclude_ids.extend(q.source_fact if isinstance(q.source_fact, list) else [q.source_fact])
            if hasattr(q, "correct_answer") and q.correct_answer:
                recent_answers = recent_answers or []
                recent_answers.append(q.correct_answer)

    facts = retrieve_relevant_facts(query, user_profile, top_k=3, exclude_ids=exclude_ids)
    prompt = build_rag_prompt(facts, recent_types, recent_answers)

    headers = {"Authorization": f"Bearer {CHUTES_API_KEY}", "Content-Type": "application/json"}
    model = "deepseek-ai/DeepSeek-R1" if provider == "deepseek" else "gpt-3.5-turbo"
    data = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 256, "temperature": 0.7, "response_format": {"type": "json_object"}}

    try:
        resp = requests.post(CHUTES_API_URL, headers=headers, json=data)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        logger.info(f"RAG raw response: {content[:200]}...")
    except Exception as e:
        logger.error(f"RAG API error: {e}")
        return generate_trivia_from_fact(get_adaptive_fact(user_profile) or get_random_fact())

    trivia = extract_first_json_object(content)
    if trivia:
        trivia["source_facts"] = [f.id for f in facts]
        return trivia
    return generate_trivia_from_fact(get_adaptive_fact(user_profile) or get_random_fact())


# ---------------------------
# Points & Scoring
# ---------------------------
def calculate_points(user_profile, trivia, is_correct, answer_time, source_fact=None):
    """Compute XP points for a trivia answer."""
    level_config = user_profile.level_config
    difficulty = level_config["difficulty"]
    base_xp = XP_VALUES[difficulty]["correct"] if is_correct else XP_VALUES[difficulty]["incorrect"]

    multiplier = 1.0

    # Combo
    if is_correct:
        user_profile.consecutive_correct += 1
        for threshold, bonus in BONUS_MULTIPLIERS["combo"].items():
            if user_profile.consecutive_correct >= threshold:
                multiplier *= bonus
    else:
        user_profile.consecutive_correct = 0

    # Time bonus
    if is_correct:
        for threshold, bonus in BONUS_MULTIPLIERS["time"].items():
            if answer_time <= threshold:
                multiplier *= bonus
                break

    # Weakness bonus
    if is_correct and source_fact and user_profile.top_weaknesses:
        fact_topics = []
        if hasattr(source_fact, "title"):
            fact_topics.append(source_fact.title)
        if hasattr(source_fact, "term"):
            fact_topics.append(source_fact.term)
        if hasattr(source_fact, "tags"):
            fact_topics.extend(getattr(source_fact, "tags", []))
        if any(topic in user_profile.top_weaknesses for topic in fact_topics):
            multiplier *= BONUS_MULTIPLIERS["weakness"]

    # Mastery
    multiplier *= BONUS_MULTIPLIERS["mastery"].get(user_profile.mastery_level, 1.0)

    # Question difficulty
    question_type = analyze_question_difficulty(trivia["question"])
    multiplier *= DIFFICULTY_WEIGHTS.get(question_type, 1.0)

    points = max(int(base_xp * multiplier), 20 if is_correct else 0)
    return points