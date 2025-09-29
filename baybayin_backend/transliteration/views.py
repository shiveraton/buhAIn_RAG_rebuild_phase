from django.shortcuts import render
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
import logging

from .services import text_transliteration_pipeline

logger = logging.getLogger(__name__)

# Create your views here.
@csrf_exempt
def transliterate_text_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Transliteration method not allowed. Use POST.'}, status=405)
    
    try: 
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
     
    text = data.get('text')
    transliteration_direction = data.get('transliteration_direction')
    source_language = data.get('source_language', 'en')  # Default to English
    
    if not text:
        return JsonResponse({'error': 'No text provided.'}, status=400)
    
    if not transliteration_direction:
        return JsonResponse({'error': 'No transliteration direction provided.'}, status=400)
    
    # Validate transliteration direction
    valid_directions = ["to_baybayin", "to_latin", "cross_en_to_baybayin"]
    if transliteration_direction not in valid_directions:
        return JsonResponse({
            'error': f'Invalid transliteration direction. Must be one of: {valid_directions}'
        }, status=400)
    
    try:
        result, warnings = text_transliteration_pipeline(
            text, transliteration_direction, source_language)

        # Build response based on transliteration type
        if transliteration_direction == "cross_en_to_baybayin":
            response_data = {
                'input_text': text,
                'transliteration_direction': transliteration_direction,
                'source_language': source_language,
                'original_text': result.get('original_text', text),
                'translated_text': result.get('translated_text', ''),
                'normalized_text': result.get('normalized_text', ''),
                'baybayin_text': result.get('baybayin_text', ''),
                'steps': result.get('steps', []),
                'warnings': warnings,
                'error': result.get('error')
            }
        else:
            # Standard transliteration response
            response_data = {
                'input_text': text,
                'transliteration_direction': transliteration_direction,
                'normalized_text': result['normalized_text'],
                'text_length': len(result['normalized_text']),
                'transliterated_text': result['transliterated_text'],
                'warnings': warnings,
                # include spell-check fields when present
                'spell_checked_text': result.get('spell_checked_text'),
                'spelling_metadata': result.get('spelling_metadata')
            }

        return JsonResponse(response_data, status=200)

    except Exception as e:
        logger.error(f"Transliteration failed: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
