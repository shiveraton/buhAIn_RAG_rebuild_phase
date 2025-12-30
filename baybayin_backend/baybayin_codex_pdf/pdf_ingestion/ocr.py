import pytesseract
import re
import logging
from ..text_sanitizer import sanitize_ocr_text

logger = logging.getLogger(__name__)

# Enhanced Tesseract configuration for Filipino/English content
TESSERACT_CONFIGS = {
    'high_quality': "--oem 1 --psm 6 -l eng+fil",  # Filipino + English
    'standard': "--oem 1 --psm 6 -l script/Latin",  # Original config
    'dense_text': "--oem 1 --psm 4 -l eng+fil",     # Dense text blocks
    'single_column': "--oem 1 --psm 5 -l eng+fil",  # Single column
    'fallback': "--oem 1 --psm 13 -l eng"           # Fallback for poor quality
}

def basic_clean_text(text):
    """Basic ligature and whitespace cleanup (legacy function)"""
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = re.sub(r"[^\S\r\n]+", " ", text)
    return text.strip()

def run_ocr_with_multiple_configs(image, return_best=True):
    """
    Run OCR with multiple configurations and return the best result
    
    Args:
        image: Input image for OCR
        return_best: If True, returns only the best result. If False, returns all results.
        
    Returns:
        If return_best=True: (raw_text, config_used)
        If return_best=False: [(raw_text, config_name), ...]
    """
    results = []
    
    for config_name, config in TESSERACT_CONFIGS.items():
        try:
            logger.debug(f"Trying OCR config: {config_name}")
            raw_text = pytesseract.image_to_string(image, config=config)
            
            # Basic quality check
            if raw_text and len(raw_text.strip()) > 0:
                results.append((raw_text, config_name))
                
        except Exception as e:
            logger.warning(f"OCR failed with config {config_name}: {str(e)}")
            continue
    
    if not results:
        logger.error("All OCR configurations failed")
        return ("", "none") if return_best else []
    
    if return_best:
        # Return the result with most content (simple heuristic)
        best_result = max(results, key=lambda x: len(x[0].strip()))
        return best_result
    
    return results

def run_ocr(image, use_sanitizer=True, ocr_config='high_quality'):
    """
    Enhanced OCR function with integrated text sanitization
    
    Args:
        image: Input image for OCR
        use_sanitizer: Whether to apply the advanced text sanitization pipeline
        ocr_config: OCR configuration to use ('high_quality', 'standard', etc.)
        
    Returns:
        If use_sanitizer=True: (cleaned_text, sanitization_stats)
        If use_sanitizer=False: cleaned_text (legacy behavior)
    """
    
    # Get OCR configuration
    if ocr_config in TESSERACT_CONFIGS:
        config = TESSERACT_CONFIGS[ocr_config]
    else:
        logger.warning(f"Unknown OCR config '{ocr_config}', using 'standard'")
        config = TESSERACT_CONFIGS['standard']
    
    try:
        # Run OCR
        logger.debug(f"Running OCR with config: {ocr_config}")
        raw_text = pytesseract.image_to_string(image, config=config)
        
        if not use_sanitizer:
            # Legacy behavior - basic cleaning only
            return basic_clean_text(raw_text)
        
        # Apply advanced sanitization pipeline
        logger.info("Applying advanced OCR text sanitization")
        cleaned_text, sanitization_stats = sanitize_ocr_text(raw_text)
        
        # Log sanitization results
        logger.info(f"Text sanitization complete - "
                   f"Original: {sanitization_stats['original_length']} chars, "
                   f"Cleaned: {sanitization_stats['cleaned_length']} chars, "
                   f"Confidence: {sanitization_stats['confidence_score']:.2f}, "
                   f"Total fixes: {sanitization_stats['total_fixes']}")
        
        return cleaned_text, sanitization_stats
        
    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        
        if use_sanitizer:
            return "", {
                'original_length': 0,
                'cleaned_length': 0,
                'unicode_errors_fixed': 0,
                'broken_words_merged': 0,
                'hyphenation_fixed': 0,
                'special_chars_removed': 0,
                'confidence_score': 0.0,
                'compression_ratio': 0.0,
                'total_fixes': 0,
                'error': str(e)
            }
        else:
            return ""

def run_ocr_with_fallback(image, use_sanitizer=True):
    """
    Run OCR with automatic fallback through different configurations
    
    Args:
        image: Input image for OCR
        use_sanitizer: Whether to apply text sanitization
        
    Returns:
        Best OCR result with metadata about which config worked
    """
    
    # Try configurations in order of preference
    config_order = ['high_quality', 'standard', 'dense_text', 'single_column', 'fallback']
    
    best_result = None
    best_confidence = 0.0
    best_config = None
    
    for config_name in config_order:
        try:
            logger.debug(f"Attempting OCR with {config_name}")
            
            if use_sanitizer:
                cleaned_text, stats = run_ocr(image, use_sanitizer=True, ocr_config=config_name)
                confidence = stats.get('confidence_score', 0.0)
                
                # If this is significantly better, use it
                if confidence > best_confidence + 0.1 or best_result is None:
                    best_result = (cleaned_text, stats)
                    best_confidence = confidence
                    best_config = config_name
                
                # If we got a good result, we can stop
                if confidence > 0.7:
                    logger.info(f"Good OCR result achieved with {config_name} (confidence: {confidence:.2f})")
                    break
                    
            else:
                # Legacy mode without sanitizer
                cleaned_text = run_ocr(image, use_sanitizer=False, ocr_config=config_name)
                if cleaned_text and len(cleaned_text.strip()) > 0:
                    best_result = cleaned_text
                    best_config = config_name
                    break
                    
        except Exception as e:
            logger.warning(f"OCR config {config_name} failed: {str(e)}")
            continue
    
    if best_result is None:
        logger.error("All OCR configurations failed")
        if use_sanitizer:
            return "", {
                'original_length': 0,
                'cleaned_length': 0,
                'confidence_score': 0.0,
                'error': 'All OCR configurations failed'
            }
        else:
            return ""
    
    logger.info(f"Best OCR result from config: {best_config}")
    
    if use_sanitizer:
        cleaned_text, stats = best_result
        stats['ocr_config_used'] = best_config
        return cleaned_text, stats
    else:
        return best_result
