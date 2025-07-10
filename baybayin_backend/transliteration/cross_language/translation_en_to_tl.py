"""
Fixed version of the translation module that has specific workarounds for model loading issues.
This will replace the problematic file if it works.
"""

import logging
import sys
import os
import time
from pathlib import Path
from functools import lru_cache

# Configure logging to stdout for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class TranslationError(Exception):
    """Custom exception for translation errors"""
    pass

# Directly import required libraries with TensorFlow avoidance
try:
    # Set environment variables to avoid TensorFlow
    os.environ['USE_TORCH'] = 'TRUE'
    os.environ['USE_TF'] = 'FALSE'
    os.environ['TRANSFORMERS_OFFLINE'] = '0'
    
    # Import minimal dependencies first
    import torch
    logger.info("✅ PyTorch imported successfully")
    
    # Import transformers with specific configurations
    import transformers
    transformers.logging.set_verbosity_error()  # Reduce logging noise
    
    # Force PyTorch-only imports to avoid TensorFlow
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    
    # Now it's safe to import MarianMT components
    from transformers import MarianMTModel, MarianTokenizer
    
    TRANSFORMERS_AVAILABLE = True
    logger.info(f"✅ Successfully imported all dependencies")
    logger.info(f"PyTorch version: {torch.__version__}")
    logger.info(f"Transformers version: {transformers.__version__}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
except ImportError as e:
    logger.error(f"❌ Failed to import required libraries: {e}")
    TRANSFORMERS_AVAILABLE = False
except Exception as e:
    logger.error(f"❌ Unexpected error during imports: {str(e)}")
    TRANSFORMERS_AVAILABLE = False

# Model configuration
MODEL_NAME = "Helsinki-NLP/opus-mt-en-tl"
MAX_LENGTH = 512
CACHE_DIR = Path(__file__).parent / "model_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Global model variables
model = None
tokenizer = None

def load_model():
    """Load the model and tokenizer with robust error handling"""
    global model, tokenizer
    
    if not TRANSFORMERS_AVAILABLE:
        logger.error("❌ Transformers library not available")
        return False
    
    try:
        # Ensure cache directory exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cache directory: {CACHE_DIR}")
        
        # Try using generic AutoTokenizer and AutoModelForSeq2SeqLM first
        try:
            logger.info(f"Loading tokenizer using AutoTokenizer for {MODEL_NAME}...")
            tokenizer = AutoTokenizer.from_pretrained(
                MODEL_NAME,
                cache_dir=CACHE_DIR,
                use_fast=True
            )
            logger.info("✅ AutoTokenizer loaded successfully")
            
            logger.info(f"Loading model using AutoModelForSeq2SeqLM for {MODEL_NAME}...")
            model = AutoModelForSeq2SeqLM.from_pretrained(
                MODEL_NAME,
                cache_dir=CACHE_DIR,
                torch_dtype=torch.float32  # Use float32 for better compatibility
            )
            logger.info("✅ AutoModel loaded successfully")
            
        except Exception as auto_error:
            logger.warning(f"Failed to load with AutoTokenizer/AutoModel: {str(auto_error)}")
            logger.info("Falling back to MarianTokenizer/MarianMTModel...")
            
            # Fallback to specific classes
            tokenizer = MarianTokenizer.from_pretrained(
                MODEL_NAME,
                cache_dir=CACHE_DIR
            )
            logger.info("✅ Tokenizer loaded successfully")
            
            model = MarianMTModel.from_pretrained(
                MODEL_NAME,
                cache_dir=CACHE_DIR
            )
            logger.info("✅ Model loaded successfully")
        
        # Move to GPU if available
        if torch.cuda.is_available():
            logger.info("Moving model to GPU...")
            model = model.cuda()
            logger.info("🚀 Model moved to GPU")
        else:
            logger.info("💻 Using CPU for inference")
        
        # Verify model loaded successfully with a simple test
        test_text = "test"
        logger.info(f"Verifying model with test text: '{test_text}'")
        inputs = tokenizer(test_text, return_tensors="pt", padding=True, truncation=True)
        if torch.cuda.is_available() and next(model.parameters()).is_cuda:
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=10)
            test_result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        logger.info(f"Test translation result: '{test_result}'")
        logger.info("✅ Model verification successful")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error loading model: {str(e)}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False

# Load model on module import
try:
    model_loaded = load_model()
    logger.info(f"Model loaded on import: {model_loaded}")
except Exception as e:
    logger.error(f"❌ Failed to load model on module import: {e}")
    model_loaded = False

def translate_text(text):
    """Simple function to translate text with minimal dependencies"""
    global model, tokenizer
    
    if not text.strip():
        return ""
    
    if model is None or tokenizer is None:
        if not load_model():
            raise TranslationError("Failed to load translation model")
    
    try:
        # Tokenize text
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=MAX_LENGTH)
        
        # Move to GPU if model is on GPU
        if torch.cuda.is_available() and next(model.parameters()).is_cuda:
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # Generate translation
        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=MAX_LENGTH, num_beams=4, early_stopping=True)
        
        # Decode output
        translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"Translation: {text} → {translation}")
        
        return translation
    except Exception as e:
        logger.error(f"❌ Translation failed: {e}")
        raise TranslationError(f"Translation failed: {e}")

# API compatibility functions
def is_translation_available():
    """Check if translation is available"""
    global model, tokenizer
    return TRANSFORMERS_AVAILABLE and model is not None and tokenizer is not None

@lru_cache(maxsize=1000)
def translate_en_to_tl(text):
    """API-compatible wrapper for translate_text with caching"""
    return translate_text(text)

def clear_translation_cache():
    """Clear translation cache"""
    translate_en_to_tl.cache_clear()

# Test the module directly if run as script
if __name__ == "__main__":
    test_text = "hello world"
    print(f"Testing translation of: '{test_text}'")
    try:
        result = translate_en_to_tl(test_text)
        print(f"Result: '{result}'")
    except Exception as e:
        print(f"Error: {e}")
