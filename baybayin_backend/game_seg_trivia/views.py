
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .content_retrieval import get_adaptive_fact
from .trivia_generator import generate_trivia_from_fact, generate_trivia_with_deepseek
from .adaptive_initializer import get_user_profile, update_user_profile

class TriviaQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get a new trivia question for the user (adaptive, LLM-powered if available).
        """
        user = request.user
        profile = get_user_profile(user)
        fact = get_adaptive_fact(profile)
        if not fact:
            return Response({"error": "No facts available."}, status=404)

        # Use LLM if requested, else fallback
        use_llm = request.query_params.get('llm', 'false').lower() == 'true'
        if use_llm:
            trivia = generate_trivia_with_deepseek(fact)
        else:
            trivia = generate_trivia_from_fact(fact)
        # Store the fact in session for answer checking (optional, for stateless API use POST)
        request.session['last_trivia'] = trivia
        return Response({"trivia": trivia})

    def post(self, request):
        """
        Submit an answer to a trivia question and update user profile.
        Expects: {"question": ..., "options": [...], "user_answer": ..., "correct_answer": ...}
        """
        user = request.user
        data = request.data
        question = {
            'question': data.get('question', ''),
            'options': data.get('options', []),
        }
        user_answer = data.get('user_answer', '')
        correct_answer = data.get('correct_answer', '')
        if not question['question'] or not user_answer or not correct_answer:
            return Response({"error": "Missing required fields."}, status=400)

        update_user_profile(user, question, user_answer, correct_answer)
        is_correct = (user_answer == correct_answer)
        return Response({"result": "correct" if is_correct else "incorrect"})