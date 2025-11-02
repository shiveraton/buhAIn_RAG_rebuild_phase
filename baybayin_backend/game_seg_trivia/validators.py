"""
Centralized validation module for trivia questions and answers.
"""
from typing import Dict, List, Any, Optional
from django.core.exceptions import ValidationError


class TriviaValidator:
    """Validates trivia question structure and content"""
    
    REQUIRED_FIELDS = ['question', 'correct_answer', 'options', 'difficulty']
    VALID_DIFFICULTIES = ['easy', 'medium', 'hard']
    MIN_OPTIONS = 2
    MAX_OPTIONS = 6
    
    @classmethod
    def validate_trivia_structure(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates the structure of a trivia question.
        
        Args:
            data: Dictionary containing trivia question data
            
        Returns:
            Validated and cleaned data
            
        Raises:
            ValidationError: If validation fails
        """
        errors = []
        
        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            raise ValidationError(errors)
        
        # Validate difficulty
        difficulty = data.get('difficulty', '').lower()
        if difficulty not in cls.VALID_DIFFICULTIES:
            errors.append(
                f"Invalid difficulty '{difficulty}'. "
                f"Must be one of: {', '.join(cls.VALID_DIFFICULTIES)}"
            )
        
        # Validate options
        options = data.get('options', [])
        if not isinstance(options, list):
            errors.append("Options must be a list")
        elif len(options) < cls.MIN_OPTIONS:
            errors.append(f"Must have at least {cls.MIN_OPTIONS} options")
        elif len(options) > cls.MAX_OPTIONS:
            errors.append(f"Cannot have more than {cls.MAX_OPTIONS} options")
        
        # Validate correct answer is in options
        correct_answer = data.get('correct_answer')
        if correct_answer and options and correct_answer not in options:
            errors.append("Correct answer must be one of the options")
        
        # Check for duplicate options
        if options and len(options) != len(set(options)):
            errors.append("Options must be unique")
        
        if errors:
            raise ValidationError(errors)
        
        # Return cleaned data
        return {
            'question': str(data['question']).strip(),
            'correct_answer': str(data['correct_answer']).strip(),
            'options': [str(opt).strip() for opt in options],
            'difficulty': difficulty,
            'source': data.get('source', ''),
            'tags': data.get('tags', []),
            'metadata': data.get('metadata', {}),
        }
    
    @classmethod
    def validate_user_answer(cls, answer: str, options: List[str]) -> str:
        """
        Validates a user's answer against available options.
        
        Args:
            answer: User's answer
            options: List of valid options
            
        Returns:
            Cleaned answer string
            
        Raises:
            ValidationError: If answer is invalid
        """
        if not answer:
            raise ValidationError("Answer cannot be empty")
        
        answer = str(answer).strip()
        
        if answer not in options:
            raise ValidationError(
                f"Invalid answer '{answer}'. Must be one of: {', '.join(options)}"
            )
        
        return answer
    
    @classmethod
    def validate_batch(cls, trivia_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validates a batch of trivia questions.
        
        Args:
            trivia_list: List of trivia question dictionaries
            
        Returns:
            List of validated trivia questions
            
        Raises:
            ValidationError: If any question fails validation
        """
        validated = []
        errors = []
        
        for idx, trivia in enumerate(trivia_list):
            try:
                validated.append(cls.validate_trivia_structure(trivia))
            except ValidationError as e:
                errors.append(f"Question {idx + 1}: {'; '.join(e.messages)}")
        
        if errors:
            raise ValidationError(errors)
        
        return validated


class AnswerValidator:
    """Validates user answers and scoring"""
    
    @staticmethod
    def is_correct(user_answer: str, correct_answer: str, 
                   case_sensitive: bool = False) -> bool:
        """
        Checks if user's answer matches the correct answer.
        
        Args:
            user_answer: User's submitted answer
            correct_answer: The correct answer
            case_sensitive: Whether comparison should be case-sensitive
            
        Returns:
            True if answers match, False otherwise
        """
        if not case_sensitive:
            user_answer = user_answer.lower().strip()
            correct_answer = correct_answer.lower().strip()
        else:
            user_answer = user_answer.strip()
            correct_answer = correct_answer.strip()
        
        return user_answer == correct_answer
    
    @staticmethod
    def calculate_score(total_questions: int, correct_answers: int) -> float:
        """
        Calculates percentage score.
        
        Args:
            total_questions: Total number of questions
            correct_answers: Number of correct answers
            
        Returns:
            Score as percentage (0-100)
        """
        if total_questions <= 0:
            return 0.0
        
        return round((correct_answers / total_questions) * 100, 2)