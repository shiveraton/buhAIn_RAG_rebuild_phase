"""
Admin Quiz Generation API Endpoints
THESIS REQUIREMENT: UC 21 - Admin Manual Quiz Generation
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from celery.result import AsyncResult
import logging

from .models import TriviaSourceFact, TriviaQuestion
from .tasks import generate_quiz_async
from .llm_service import get_llm_service
from .validators import validate_llm_question

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class GenerateQuizView(APIView):
    """
    Admin endpoint to generate trivia quiz using Deepseek LLM
    POST: Trigger async quiz generation
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        """
        Generate quiz asynchronously from source facts
        
        Request body:
        {
            "source_fact_ids": ["uuid1", "uuid2", ...],  // Optional - if empty, uses all facts
            "max_questions": 5,  // Optional - default 5
            "difficulty": "medium",  // Optional - easy, medium, hard
            "question_type": "basic_fact",  // Optional
            "async": true  // Optional - if false, generates synchronously
        }
        
        Response:
        {
            "task_id": "celery-task-uuid",
            "status": "PENDING",
            "message": "Quiz generation started"
        }
        """
        logger.info(f"Admin quiz generation request from user: {request.user}")
        
        # Parse request parameters
        source_fact_ids = request.data.get('source_fact_ids', [])
        max_questions = request.data.get('max_questions', 5)
        difficulty = request.data.get('difficulty', 'medium')
        question_type = request.data.get('question_type', 'basic_fact')
        use_async = request.data.get('async', True)
        
        # Validate parameters
        if max_questions < 1 or max_questions > 50:
            return Response(
                {'error': 'max_questions must be between 1 and 50'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if difficulty not in ['easy', 'medium', 'hard']:
            return Response(
                {'error': 'difficulty must be easy, medium, or hard'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If no source_fact_ids provided, get random facts
        if not source_fact_ids:
            random_facts = TriviaSourceFact.objects.all().order_by('?')[:max_questions]
            source_fact_ids = [str(fact.id) for fact in random_facts]
            logger.info(f"No source_fact_ids provided, selected {len(source_fact_ids)} random facts")
        
        if not source_fact_ids:
            return Response(
                {'error': 'No source facts available. Please ingest content first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Trigger async task or generate synchronously
        if use_async:
            logger.info(f"Triggering async quiz generation: {max_questions} questions")
            task = generate_quiz_async.delay(
                source_fact_ids=source_fact_ids,
                max_questions=max_questions,
                difficulty=difficulty,
                question_type=question_type
            )
            
            return Response({
                'task_id': task.id,
                'status': task.state,
                'message': f'Quiz generation started for {max_questions} questions',
                'source_facts_count': len(source_fact_ids)
            }, status=status.HTTP_202_ACCEPTED)
        
        else:
            # Synchronous generation (for small batches)
            logger.info(f"Generating quiz synchronously: {max_questions} questions")
            
            llm_service = get_llm_service()
            generated_questions = []
            errors = []
            
            for i, fact_id in enumerate(source_fact_ids[:max_questions]):
                try:
                    # Get source fact
                    source_fact = TriviaSourceFact.objects.get(id=fact_id)
                    
                    # Generate question
                    llm_output = llm_service.generate_trivia_question(
                        context=source_fact.content,
                        difficulty=difficulty,
                        question_type=question_type
                    )
                    
                    # Validate
                    validation_result = validate_llm_question(llm_output)
                    
                    if not validation_result.is_valid:
                        error_msg = f"Validation failed for question {i+1}: {', '.join(validation_result.errors)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue
                    
                    # Save
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
                        source_fact=source_fact,
                        tags=validated_data.get('tags', []),
                        generated_by_llm=True
                    )
                    
                    generated_questions.append(str(question.id))
                    logger.info(f"✅ Generated question {i+1}/{max_questions}")
                    
                except Exception as e:
                    error_msg = f"Error generating question {i+1}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)
            
            return Response({
                'success': len(generated_questions) > 0,
                'questions_generated': len(generated_questions),
                'question_ids': generated_questions,
                'errors': errors
            }, status=status.HTTP_200_OK if len(generated_questions) > 0 else status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class QuizTaskStatusView(APIView):
    """
    Check the status of an async quiz generation task
    GET: Get task status and results
    """
    permission_classes = [IsAdminUser]

    def get(self, request, task_id):
        """
        Get status of async quiz generation task
        
        Response:
        {
            "task_id": "uuid",
            "state": "PENDING|PROCESSING|SUCCESS|FAILURE",
            "result": {...},  // If complete
            "progress": {"current": 3, "total": 5}  // If processing
        }
        """
        logger.info(f"Task status check: {task_id}")
        
        task = AsyncResult(task_id)
        
        response_data = {
            'task_id': task_id,
            'state': task.state
        }
        
        if task.state == 'PENDING':
            response_data['message'] = 'Task is waiting to be processed'
        
        elif task.state == 'PROCESSING':
            response_data['message'] = 'Task is currently processing'
            response_data['progress'] = task.info  # Contains current/total
        
        elif task.state == 'SUCCESS':
            response_data['message'] = 'Task completed successfully'
            response_data['result'] = task.result
        
        elif task.state == 'FAILURE':
            response_data['message'] = 'Task failed'
            response_data['error'] = str(task.info)
        
        else:
            response_data['message'] = f'Unknown state: {task.state}'
        
        return Response(response_data, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class SourceFactsListView(APIView):
    """
    List available source facts for quiz generation
    GET: Get paginated list of source facts
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        List source facts with filtering and pagination
        
        Query params:
        - page: int (default 1)
        - page_size: int (default 20, max 100)
        - search: str (search in content)
        - tags: str (comma-separated tags to filter by)
        """
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        search = request.GET.get('search', '')
        tags_str = request.GET.get('tags', '')
        
        # Build queryset
        queryset = TriviaSourceFact.objects.all()
        
        if search:
            queryset = queryset.filter(content__icontains=search)
        
        if tags_str:
            tags = [tag.strip() for tag in tags_str.split(',')]
            for tag in tags:
                queryset = queryset.filter(tags__contains=[tag])
        
        # Count and paginate
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        facts = queryset[start:end]
        
        # Serialize
        facts_data = [
            {
                'id': str(fact.id),
                'content': fact.content[:200] + '...' if len(fact.content) > 200 else fact.content,
                'tags': fact.tags,
                'has_embedding': bool(fact.get_embedding() is not None),
                'created_at': fact.created_at.isoformat() if hasattr(fact, 'created_at') else None
            }
            for fact in facts
        ]
        
        return Response({
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'facts': facts_data
        }, status=status.HTTP_200_OK)
