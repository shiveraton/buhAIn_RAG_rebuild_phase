# baybayin_backend/game_seg_trivia/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from game_seg_trivia.game_config import LEVELS

class UserTriviaProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_answered = models.IntegerField(default=0)
    total_correct = models.IntegerField(default=0)
    total_incorrect = models.IntegerField(default=0)
    last_played = models.DateTimeField(null=True, blank=True)
    
    # Adaptive learning fields
    weaknesses = models.JSONField(default=dict, help_text="Dictionary of topics with error counts")
    top_weaknesses = models.JSONField(default=list, help_text="Top 3 weak areas")
    
    # Learning progress tracking
    mastery_level = models.IntegerField(default=1, help_text="User's Baybayin mastery level (1-10)")
    
    # Level progression
    current_level = models.IntegerField(default=1)
    current_xp = models.IntegerField(default=0)
    moves_remaining = models.IntegerField(default=0)
    consecutive_correct = models.IntegerField(default=0)
    
    # Session tracking
    session_start = models.DateTimeField(auto_now_add=True)
    session_moves = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username}'s Trivia Profile"
    
    @property
    def accuracy_rate(self):
        if self.total_answered == 0:
            return 0
        return round((self.total_correct / self.total_answered) * 100, 1)
    
    def initialize_level(self):
        """Reset level parameters when starting a new level"""
        level_config = LEVELS.get(self.current_level, LEVELS[10])
        self.moves_remaining = level_config["max_moves"]
        self.current_xp = 0
        self.consecutive_correct = 0
        self.session_moves = 0
        self.save()
        
    def complete_level(self):
        """Handle level completion"""
        self.current_level = min(self.current_level + 1, 10)
        self.initialize_level()
        
    def fail_level(self):
        """Handle level failure"""
        self.initialize_level()
        
    @property
    def level_progress(self):
        """Calculate progress percentage for current level"""
        target = LEVELS.get(self.current_level, {}).get("target_xp", 1)
        return min(100, int((self.current_xp / target) * 100))
    
    @property
    def level_config(self):
        return LEVELS.get(self.current_level, LEVELS[10])

class TriviaQuestionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question_text = models.TextField()
    options = models.JSONField()
    correct_answer = models.CharField(max_length=200)
    user_answer = models.CharField(max_length=200)
    is_correct = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Question type categorization
    QUESTION_TYPE_CHOICES = [
        ('basic_fact', 'Basic Fact'),
        ('historical_context', 'Historical Context'),
        ('linguistic_analysis', 'Linguistic Analysis'),
        ('comparative_analysis', 'Comparative Analysis'),
    ]
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPE_CHOICES, default='basic_fact')
    
    # Reference to the fact(s) used
    source_fact = models.JSONField(
        null=True, 
        blank=True,
        help_text="ID and type of source fact(s) used"
    )
    
    def __str__(self):
        return f"Question on {self.timestamp.strftime('%Y-%m-%d')}"