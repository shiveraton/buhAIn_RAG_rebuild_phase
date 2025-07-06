from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .checker import TagalogSpellingChecker
import os

@csrf_exempt
def check_spelling(request):
    if request.method == "POST":
        data = json.loads(request.body)
        word = data.get("word", "").strip()
        dict_path = os.path.join(os.path.dirname(__file__), "data", "tagalog_dictionary.txt")
        checker = TagalogSpellingChecker(dict_path, use_online=True)
        is_correct = checker.is_correct(word)
        suggestions = checker.suggest(word) if not is_correct else []
        return JsonResponse({
            "word": word,
            "is_correct": is_correct,
            "suggestions": suggestions
        })
    return JsonResponse({"error": "POST required"}, status=405)