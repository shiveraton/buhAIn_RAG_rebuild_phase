
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserTriviaProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trivia_profile')
    total_answered = models.PositiveIntegerField(default=0)
    total_correct = models.PositiveIntegerField(default=0)
    total_incorrect = models.PositiveIntegerField(default=0)
    last_played = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"TriviaProfile({self.user.username})"

    @property
    def accuracy(self):
        if self.total_answered == 0:
            return 0.0
        return self.total_correct / self.total_answered

class TriviaQuestionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trivia_history')
    question = models.TextField()
    options = models.JSONField()
    correct_answer = models.CharField(max_length=255)
    user_answer = models.CharField(max_length=255)
    is_correct = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.question[:50]}... ({'correct' if self.is_correct else 'wrong'})"
