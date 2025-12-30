"""
Centralized validation module for trivia questions and answers.
UPDATED: Added Pydantic-based LLM output validation (Thesis Requirement)
"""
from typing import Dict, List, Any, Optional
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import BaseModel, Field, validator, ValidationError
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# LLM Output Validation (Thesis Requirement - JSON Schema Conformance)
# ============================================================================

class TriviaQuestionSchema(BaseModel):
    """
    Pydantic model for validating LLM-generated trivia questions
    Enforces thesis-mandated JSON schema structure
    """
    
    question: str = Field(
        ..., 
        min_length=10,
        max_length=500,
        description="The trivia question text"
    )
    
    correct_answer: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The correct answer"
    )
    
    wrong_answers: List[str] = Field(
        ...,
        min_items=3,
        max_items=3,
        description="Exactly three incorrect but plausible answers"
    )
    
    explanation: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Explanation of why the correct answer is correct"
    )
    
    difficulty: str = Field(
        ...,
        description="Question difficulty level"
    )
    
    question_type: str = Field(
        ...,
        description="Category of question for adaptive learning"
    )
    
    tags: List[str] = Field(
        default_factory=list,
        description="Relevant tags/keywords for the question"
    )
    
    @validator('difficulty')
    def validate_difficulty(cls, v):
        """Ensure difficulty is one of the allowed values"""
        allowed = ['easy', 'medium', 'hard']
        if v not in allowed:
            raise ValueError(f"Difficulty must be one of {allowed}, got '{v}'")
        return v
    
    @validator('question_type')
    def validate_question_type(cls, v):
        """Ensure question_type is one of the allowed values"""
        allowed = ['basic_fact', 'historical_context', 'linguistic_analysis', 'comparative_analysis']
        if v not in allowed:
            raise ValueError(f"Question type must be one of {allowed}, got '{v}'")
        return v
    
    @validator('wrong_answers')
    def validate_wrong_answers(cls, v):
        """Ensure exactly 3 unique wrong answers"""
        if len(v) != 3:
            raise ValueError(f"Must have exactly 3 wrong answers, got {len(v)}")
        
        # Check for uniqueness
        if len(set(v)) != 3:
            raise ValueError("Wrong answers must be unique")
        
        # Check each answer is non-empty
        for answer in v:
            if not answer.strip():
                raise ValueError("Wrong answers cannot be empty")
        
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Ensure tags are non-empty and unique"""
        if v:
            # Remove empty tags
            v = [tag.strip() for tag in v if tag.strip()]
            # Remove duplicates while preserving order
            seen = set()
            v = [tag for tag in v if not (tag in seen or seen.add(tag))]
        return v
    
    class Config:
        """Pydantic configuration"""
        str_strip_whitespace = True
        validate_assignment = True


class ValidationResult(BaseModel):
    """Result of LLM output validation operation"""
    is_valid: bool
    validated_data: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def validate_llm_question(question_data: Dict[str, Any]) -> ValidationResult:
    """
    Validate LLM-generated trivia question against thesis schema (CRITICAL)
    
    Args:
        question_data: Dictionary with question data from LLM
    
    Returns:
        ValidationResult with is_valid, validated_data, and any errors
    """
    try:
        # Validate using Pydantic model
        validated = TriviaQuestionSchema(**question_data)
        
        # Additional business logic validations
        warnings = []
        
        # Check if correct answer appears in wrong answers
        if validated.correct_answer in validated.wrong_answers:
            warnings.append("Correct answer should not appear in wrong answers")
        
        # Check answer length consistency
        avg_length = sum(len(ans) for ans in validated.wrong_answers) / 3
        if len(validated.correct_answer) > avg_length * 3:
            warnings.append("Correct answer is significantly longer than wrong answers")
        
        # Check if question ends with question mark
        if not validated.question.strip().endswith('?'):
            warnings.append("Question should end with a question mark")
        
        logger.info(f"LLM output validated successfully: {validated.question[:50]}...")
        
        return ValidationResult(
            is_valid=True,
            validated_data=validated.dict(),
            errors=[],
            warnings=warnings
        )
        
    except ValidationError as e:
        # Extract error messages
        errors = []
        for error in e.errors():
            field = ' -> '.join(str(x) for x in error['loc'])
            message = error['msg']
            errors.append(f"{field}: {message}")
        
        logger.error(f"LLM output validation failed: {errors}")
        
        return ValidationResult(
            is_valid=False,
            validated_data=None,
            errors=errors,
            warnings=[]
        )
    
    except Exception as e:
        logger.error(f"Unexpected validation error: {e}")
        return ValidationResult(
            is_valid=False,
            validated_data=None,
            errors=[f"Unexpected error: {str(e)}"],
            warnings=[]
        )


def validate_multiple_llm_questions(questions_data: List[Dict[str, Any]]) -> List[ValidationResult]:
    """
    Validate multiple LLM-generated trivia questions
    
    Args:
        questions_data: List of question dictionaries from LLM
    
    Returns:
        List of ValidationResult objects
    """
    results = []
    
    for i, question_data in enumerate(questions_data):
        logger.info(f"Validating LLM question {i+1}/{len(questions_data)}")
        result = validate_llm_question(question_data)
        results.append(result)
    
    valid_count = sum(1 for r in results if r.is_valid)
    logger.info(f"Validated {valid_count}/{len(questions_data)} LLM questions successfully")
    
    return results


# ============================================================================
# Legacy Django Validation (Backward Compatibility)
# ============================================================================


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