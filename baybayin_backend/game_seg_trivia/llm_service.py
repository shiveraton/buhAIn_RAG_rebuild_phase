"""
Deepseek-R1 LLM Service for Trivia Question Generation
THESIS REQUIREMENT: LLM integration with mandated JSON schema output
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI  # Deepseek uses OpenAI-compatible API
from django.conf import settings

logger = logging.getLogger(__name__)


class DeepseekLLMService:
    """
    LLM Service using Deepseek-R1 for trivia question generation
    Implements thesis-mandated JSON schema output structure
    """
    
    def __init__(self):
        """Initialize Deepseek client with API key from settings"""
        self.api_key = getattr(settings, 'DEEPSEEK_API_KEY', os.getenv('DEEPSEEK_API_KEY'))
        
        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY not configured. LLM service will not work.")
            self.client = None
        else:
            # Deepseek uses OpenAI-compatible API
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
            logger.info("Deepseek LLM Service initialized successfully")
        
        # Thesis-mandated JSON schema for question generation
        self.question_schema = {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The trivia question text"},
                "correct_answer": {"type": "string", "description": "The correct answer"},
                "wrong_answers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 3,
                    "description": "Three incorrect but plausible answers"
                },
                "explanation": {"type": "string", "description": "Explanation of why the correct answer is correct"},
                "difficulty": {
                    "type": "string",
                    "enum": ["easy", "medium", "hard"],
                    "description": "Question difficulty level"
                },
                "question_type": {
                    "type": "string",
                    "enum": ["basic_fact", "historical_context", "linguistic_analysis", "comparative_analysis"],
                    "description": "Category of question"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Relevant tags/keywords for the question"
                }
            },
            "required": ["question", "correct_answer", "wrong_answers", "explanation", "difficulty", "question_type", "tags"]
        }
    
    def generate_trivia_question(
        self, 
        context: str, 
        difficulty: str = "medium",
        question_type: str = "basic_fact",
        model: str = "deepseek-reasoner"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a trivia question from given context using Deepseek-R1
        
        Args:
            context: Source text to generate question from
            difficulty: Desired difficulty level (easy/medium/hard)
            question_type: Type of question to generate
            model: Deepseek model to use (deepseek-reasoner or deepseek-chat)
        
        Returns:
            Dictionary with question data conforming to JSON schema, or None if generation fails
        """
        if not self.client:
            logger.error("Deepseek client not initialized. Check API key configuration.")
            return None
        
        try:
            # Construct prompt with JSON schema requirements
            prompt = self._build_prompt(context, difficulty, question_type)
            
            logger.info(f"Generating {difficulty} {question_type} question using {model}")
            
            # Call Deepseek API
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}  # Ensure JSON output
            )
            
            # Extract and parse response
            raw_content = response.choices[0].message.content
            logger.debug(f"Raw LLM response: {raw_content}")
            
            # Parse JSON response
            question_data = json.loads(raw_content)
            
            logger.info(f"Successfully generated question: {question_data.get('question', '')[:50]}...")
            return question_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw response: {raw_content}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating trivia question: {e}")
            return None
    
    def generate_multiple_questions(
        self,
        contexts: List[str],
        difficulty: str = "medium",
        question_type: str = "basic_fact",
        max_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple trivia questions from multiple contexts
        
        Args:
            contexts: List of source texts
            difficulty: Desired difficulty level
            question_type: Type of questions to generate
            max_questions: Maximum number of questions to generate
        
        Returns:
            List of question dictionaries
        """
        questions = []
        
        for i, context in enumerate(contexts[:max_questions]):
            logger.info(f"Generating question {i+1}/{min(len(contexts), max_questions)}")
            
            question = self.generate_trivia_question(
                context=context,
                difficulty=difficulty,
                question_type=question_type
            )
            
            if question:
                questions.append(question)
        
        logger.info(f"Successfully generated {len(questions)} questions")
        return questions
    
    def _get_system_prompt(self) -> str:
        """System prompt defining LLM behavior and output requirements"""
        return """You are an expert educational content creator specializing in Baybayin script and Philippine linguistics.

Your task is to generate high-quality trivia questions in STRICT JSON format based on provided context.

CRITICAL REQUIREMENTS:
1. Output MUST be valid JSON conforming to the specified schema
2. Questions must be clear, unambiguous, and factually accurate
3. Wrong answers must be plausible but clearly incorrect
4. Explanations must be educational and cite the source context
5. Use appropriate Filipino/Tagalog terminology when relevant

OUTPUT ONLY valid JSON. No markdown, no code blocks, no additional text."""
    
    def _build_prompt(self, context: str, difficulty: str, question_type: str) -> str:
        """Build the user prompt with context and requirements"""
        return f"""Generate a {difficulty} difficulty trivia question of type "{question_type}" based on the following context about Baybayin:

CONTEXT:
{context}

Generate a JSON object with the following structure:
{{
    "question": "The trivia question text (clear and specific)",
    "correct_answer": "The correct answer (concise)",
    "wrong_answers": ["Wrong answer 1", "Wrong answer 2", "Wrong answer 3"],
    "explanation": "Explanation of why the correct answer is right, citing the context",
    "difficulty": "{difficulty}",
    "question_type": "{question_type}",
    "tags": ["relevant", "tags", "here"]
}}

IMPORTANT: Output ONLY the JSON object, nothing else."""

    def get_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for validation"""
        return self.question_schema


# Singleton instance
_llm_service = None

def get_llm_service() -> DeepseekLLMService:
    """Get or create singleton LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = DeepseekLLMService()
    return _llm_service
