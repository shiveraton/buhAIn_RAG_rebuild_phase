from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .services import spelling_check_pipeline

@csrf_exempt
def check_spelling(request):
    if request.method == "POST":
        data = json.loads(request.body)
        word = data.get("word", "").strip()
        result = spelling_check_pipeline(word)
        return JsonResponse(result)
    return JsonResponse({"error": "POST required"}, status=405)