from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from image_transliteration.services.pipeline_service import image_transliteration_pipeline

@csrf_exempt
def transliterate_image_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed. Use POST.'}, status=405)
    
    # params = {}
    # for key, value in data.items():
    #     if key != "model":
    #         params[key] = value

    image_file = request.FILES.get('inputImage')
    direction = request.POST.get('direction')
    role = request.POST.get('role')

    if not image_file:
        return JsonResponse({'error': 'No image provided'}, status=400)
    
    predicted_text = image_transliteration_pipeline(image_file, direction, role)
    
    if predicted_text is None:
        return JsonResponse({'error': 'Prediction failed'}, status=200)
    
    return JsonResponse({'predicted_text': predicted_text}, status=200)
