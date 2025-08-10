# baybayin_backend/game_seg_trivia/adaptive_initializer.py
from .models import UserTriviaProfile, TriviaQuestionHistory
from django.utils import timezone

def get_user_profile(user):
    """Retrieve or create the user's trivia profile"""
    profile, created = UserTriviaProfile.objects.get_or_create(user=user)
    return profile

def update_user_profile(user, question, user_answer, correct_answer, source_fact=None, question_type='basic_fact'):
    """
    Update the user's trivia profile with adaptive learning:
    - Track correct/incorrect answers
    - Identify weak areas
    - Log question history with fact references
    """
    profile = get_user_profile(user)
    profile.total_answered += 1
    
    # Determine correctness
    is_correct = (user_answer.lower() == correct_answer.lower())
    if is_correct:
        profile.total_correct += 1
    else:
        profile.total_incorrect += 1
        # Update weaknesses based on incorrect answers
        
        # Extract topics from source fact(s)
        topics = []
        if source_fact:
            # Handle single fact
            if hasattr(source_fact, 'title'):
                topics.append(source_fact.title)
            elif hasattr(source_fact, 'term'):
                topics.append(source_fact.term)
            
            # Handle list of facts (from RAG)
            elif isinstance(source_fact, list):
                for fact_id in source_fact:
                    # In a real implementation, we'd fetch the fact
                    # For now, just track the ID
                    topics.append(f"fact_{fact_id}")
        
        # Update weaknesses
        if topics:
            if not profile.weaknesses:
                profile.weaknesses = {}
                
            for topic in topics:
                profile.weaknesses[topic] = profile.weaknesses.get(topic, 0) + 1
    
    profile.last_played = timezone.now()
    profile.save()

    # Log question history
    TriviaQuestionHistory.objects.create(
        user=user,
        question_text=question.get('question', ''),
        options=question.get('options', []),
        correct_answer=correct_answer,
        user_answer=user_answer,
        is_correct=is_correct,
        source_fact=source_fact,
        question_type=question_type
    )
    
    # Update weakness tracking (keep top 3 weak areas)
    if profile.weaknesses:
        # Sort weaknesses by error count
        sorted_weaknesses = sorted(
            profile.weaknesses.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        # Keep only top 3 weak areas
        profile.top_weaknesses = [topic for topic, count in sorted_weaknesses[:3]]
        profile.save()

def update_mastery_level(user_profile):
    """Update mastery based on overall performance"""
    if user_profile.total_answered < 20:
        return  # Not enough data
    
    accuracy = user_profile.accuracy_rate
    
    # Determine mastery level
    if accuracy >= 90 and user_profile.current_level >= 8:
        new_level = 10  # Grandmaster
    elif accuracy >= 85 and user_profile.current_level >= 6:
        new_level = 9   # Master
    elif accuracy >= 80 and user_profile.current_level >= 5:
        new_level = 8   # Expert
    elif accuracy >= 75 and user_profile.current_level >= 4:
        new_level = 7   # Advanced
    elif accuracy >= 70:
        new_level = 6   # Intermediate
    elif accuracy >= 60:
        new_level = 5
    elif accuracy >= 50:
        new_level = 4
    elif accuracy >= 40:
        new_level = 3
    elif accuracy >= 30:
        new_level = 2
    else:
        new_level = 1
    
    # Apply with some hysteresis
    if new_level > user_profile.mastery_level:
        user_profile.mastery_level = min(user_profile.mastery_level + 1, new_level)
    elif new_level < user_profile.mastery_level - 1:
        user_profile.mastery_level = max(1, user_profile.mastery_level - 1)
    
    user_profile.save()