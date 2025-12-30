"""
Celery tasks for asynchronous trivia generation
THESIS REQUIREMENT: Async processing for quiz generation (UC 21)
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from typing import List, Dict, Any
import json

from .models import TriviaSourceFact, TriviaQuestion
from .llm_service import get_llm_service
from .validators import validate_llm_question

logger = get_task_logger(__name__)


@shared_task(bind=True, name='game_seg_trivia.generate_quiz_async')
def generate_quiz_async(
    self,
    source_fact_ids: List[str],
    max_questions: int = 5,
    difficulty: str = 'medium',
    question_type: str = 'basic_fact'
) -> Dict[str, Any]:
    """
    Generate trivia quiz asynchronously using Deepseek LLM
    
    Args:
        source_fact_ids: List of TriviaSourceFact IDs to generate questions from
        max_questions: Maximum number of questions to generate
        difficulty: Question difficulty level (easy, medium, hard)
        question_type: Type of question (basic_fact, historical_context, etc.)
    
    Returns:
        Dict with:
            - success: bool
            - questions_generated: int
            - question_ids: List[str]
            - errors: List[str]
    """
    logger.info(f"Starting quiz generation task: {max_questions} questions from {len(source_fact_ids)} sources")
    
    # Update task progress
    self.update_state(state='PROCESSING', meta={'current': 0, 'total': max_questions})
    
    llm_service = get_llm_service()
    generated_questions = []
    errors = []
    
    try:
        # Retrieve source facts
        source_facts = TriviaSourceFact.objects.filter(id__in=source_fact_ids)
        
        if not source_facts.exists():
            logger.error(f"No source facts found for IDs: {source_fact_ids}")
            return {
                'success': False,
                'questions_generated': 0,
                'question_ids': [],
                'errors': ['No valid source facts found']
            }
        
        logger.info(f"Retrieved {source_facts.count()} source facts")
        
        # Generate questions from each source fact
        for i, source_fact in enumerate(source_facts[:max_questions]):
            try:
                logger.info(f"Generating quiz {i+1}/{max_questions} from source: {source_fact.id}")
                
                # Update progress
                self.update_state(
                    state='PROCESSING',
                    meta={
                        'current': i + 1,
                        'total': max_questions,
                        'source_fact': str(source_fact.id)
                    }
                )
                
                # Generate question using LLM
                llm_output = llm_service.generate_trivia_question(
                    context=source_fact.content,
                    difficulty=difficulty,
                    question_type=question_type
                )
                
                logger.info(f"LLM generated question: {llm_output.get('question', '')[:50]}...")
                
                # Validate LLM output (THESIS REQUIREMENT)
                validation_result = validate_llm_question(llm_output)
                
                if not validation_result.is_valid:
                    error_msg = f"Validation failed for question {i+1}: {', '.join(validation_result.errors)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
                
                # Log warnings if any
                if validation_result.warnings:
                    logger.warning(f"Validation warnings: {', '.join(validation_result.warnings)}")
                
                # Save validated question to database with traceability (Golden Thread)
                validated_data = validation_result.validated_data
                
                question = TriviaQuestion.objects.create(
                    question=validated_data['question'],
                    correct_answer=validated_data['correct_answer'],
                    wrong_answer_1=validated_data['wrong_answers'][0],
                    wrong_answer_2=validated_data['wrong_answers'][1],
                    wrong_answer_3=validated_data['wrong_answers'][2],
                    explanation=validated_data['explanation'],
                    difficulty=validated_data['difficulty'],
                    question_type=validated_data['question_type'],
                    source_fact=source_fact,  # GOLDEN THREAD: Link to source
                    tags=validated_data.get('tags', []),
                    generated_by_llm=True
                )
                
                generated_questions.append(str(question.id))
                logger.info(f"✅ Successfully saved question {question.id}")
                
            except Exception as e:
                error_msg = f"Error generating question {i+1}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
                continue
        
        logger.info(f"Quiz generation complete: {len(generated_questions)}/{max_questions} questions")
        
        return {
            'success': len(generated_questions) > 0,
            'questions_generated': len(generated_questions),
            'question_ids': generated_questions,
            'errors': errors
        }
        
    except Exception as e:
        logger.error(f"Fatal error in quiz generation task: {str(e)}", exc_info=True)
        return {
            'success': False,
            'questions_generated': 0,
            'question_ids': [],
            'errors': [str(e)]
        }


@shared_task(bind=True, name='game_seg_trivia.generate_adaptive_question')
def generate_adaptive_question_async(
    self,
    user_id: str,
    topic: str = None,
    difficulty: str = None
) -> Dict[str, Any]:
    """
    Generate adaptive trivia question based on user performance
    
    Args:
        user_id: User ID for adaptive difficulty
        topic: Optional topic filter
        difficulty: Optional explicit difficulty
    
    Returns:
        Dict with question data or error
    """
    logger.info(f"Generating adaptive question for user {user_id}")
    
    # TODO: Implement adaptive difficulty calculation
    # For now, use medium difficulty
    difficulty = difficulty or 'medium'
    
    # Get random source fact
    # TODO: Filter by topic and user mastery level
    source_facts = TriviaSourceFact.objects.all()
    
    if topic:
        source_facts = source_facts.filter(tags__contains=[topic])
    
    if not source_facts.exists():
        return {
            'success': False,
            'error': 'No source facts available'
        }
    
    source_fact = source_facts.order_by('?').first()
    
    # Generate single question
    result = generate_quiz_async(
        self,
        source_fact_ids=[str(source_fact.id)],
        max_questions=1,
        difficulty=difficulty
    )
    
    if result['success'] and result['question_ids']:
        question_id = result['question_ids'][0]
        question = TriviaQuestion.objects.get(id=question_id)
        
        return {
            'success': True,
            'question': {
                'id': str(question.id),
                'question': question.question,
                'correct_answer': question.correct_answer,
                'wrong_answers': [
                    question.wrong_answer_1,
                    question.wrong_answer_2,
                    question.wrong_answer_3
                ],
                'difficulty': question.difficulty,
                'question_type': question.question_type
            }
        }
    
    return {
        'success': False,
        'error': result.get('errors', ['Unknown error'])
    }
