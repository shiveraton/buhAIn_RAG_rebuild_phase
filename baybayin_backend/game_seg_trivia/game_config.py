# baybayin_backend/game_seg_trivia/game_config.py

# Level progression configuration
LEVELS = {
    1: {"target_xp": 300, "max_moves": 12, "difficulty": "beginner"},
    2: {"target_xp": 600, "max_moves": 15, "difficulty": "beginner"},
    3: {"target_xp": 1000, "max_moves": 18, "difficulty": "intermediate"},
    4: {"target_xp": 1600, "max_moves": 20, "difficulty": "intermediate"},
    5: {"target_xp": 2400, "max_moves": 22, "difficulty": "advanced"},
    6: {"target_xp": 3400, "max_moves": 25, "difficulty": "advanced"},
    7: {"target_xp": 4600, "max_moves": 28, "difficulty": "expert"},
    8: {"target_xp": 6000, "max_moves": 30, "difficulty": "expert"},
    9: {"target_xp": 7600, "max_moves": 30, "difficulty": "master"},
    10: {"target_xp": 9500, "max_moves": 35, "difficulty": "grandmaster"},
}

# XP values per difficulty level
XP_VALUES = {
    "beginner": {"correct": 80, "incorrect": -5},
    "intermediate": {"correct": 120, "incorrect": -8},
    "advanced": {"correct": 180, "incorrect": -12},
    "expert": {"correct": 250, "incorrect": -15},
    "master": {"correct": 350, "incorrect": -20},
    "grandmaster": {"correct": 500, "incorrect": -25},
}

# Bonus multipliers
BONUS_MULTIPLIERS = {
    "combo": {3: 1.3, 5: 1.6, 8: 2.0},
    "time": {5: 1.5, 10: 1.3, 20: 1.1},
    "weakness": 2.0,
    "mastery": {
        1: 1.0, 2: 1.2, 3: 1.4, 
        4: 1.6, 5: 1.8, 6: 2.0,
        7: 2.3, 8: 2.6, 9: 3.0, 10: 3.5
    }
}

# Question difficulty weighting
DIFFICULTY_WEIGHTS = {
    "basic_fact": 1.0,
    "historical_context": 1.3,
    "linguistic_analysis": 1.7,
    "comparative_analysis": 2.0
}

# Question type categories
QUESTION_TYPES = [
    "basic_fact",
    "historical_context",
    "linguistic_analysis",
    "comparative_analysis"
]