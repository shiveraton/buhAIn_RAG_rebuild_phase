
from .models import UserTriviaProfile, TriviaQuestionHistory
from django.utils import timezone

def get_user_profile(user):
    """
    Retrieve or create the user's trivia profile.
    """
    profile, created = UserTriviaProfile.objects.get_or_create(user=user)
    return profile

def update_user_profile(user, question, user_answer, correct_answer):
    """
    Update the user's trivia profile and log the question history.
    """
    profile = get_user_profile(user)
    profile.total_answered += 1
    is_correct = (user_answer == correct_answer)
    if is_correct:
        profile.total_correct += 1
    else:
        profile.total_incorrect += 1
    profile.last_played = timezone.now()
    profile.save()

    # Log question history
    TriviaQuestionHistory.objects.create(
        user=user,
        question=question.get('question', ''),
        options=question.get('options', []),
        correct_answer=correct_answer,
        user_answer=user_answer,
        is_correct=is_correct
    )