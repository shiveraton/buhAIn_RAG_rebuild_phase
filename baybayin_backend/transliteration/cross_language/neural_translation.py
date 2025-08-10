"""
Production-grade English-Tagalog translation using fine-tuned MarianMT
"""
import logging
import sys
from transformers import MarianMTModel, MarianTokenizer, pipeline
from functools import lru_cache
import torch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class TranslationError(Exception):
    """Custom exception for translation errors"""
    pass

class NeuralTranslator:
    def __init__(self, model_path: str = None):
        # Try to use fine-tuned model if available, else fallback to base MarianMT
        import os
        default_finetuned = os.path.join(os.path.dirname(__file__), '../../data/translation/en-tl-marianmt/')
        default_finetuned = os.path.abspath(default_finetuned)
        base_model = "Helsinki-NLP/opus-mt-en-tl"
        def is_valid_marianmt_dir(path):
            required_files = ["config.json", "pytorch_model.bin", "tokenizer_config.json", "source.spm", "target.spm"]
            return os.path.isdir(path) and all(os.path.isfile(os.path.join(path, f)) for f in required_files)
        if model_path is None:
            model_path = default_finetuned if is_valid_marianmt_dir(default_finetuned) else base_model
        try:
            self.tokenizer = MarianTokenizer.from_pretrained(model_path)
            self.model = MarianMTModel.from_pretrained(model_path)
            self.translator = pipeline(
                "translation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info(f"Loaded translation model from {model_path}")
            logger.info(f"Using {'GPU' if torch.cuda.is_available() else 'CPU'}")
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            raise TranslationError(f"Initialization error: {e}") from e

    @lru_cache(maxsize=500)
    def translate(self, text: str) -> str:
        """Translate English to Tagalog with neural MT"""
        if not text.strip():
            return ""
        try:
            result = self.translator(
                text,
                max_length=512,
                num_beams=5,
                early_stopping=True,
                clean_up_tokenization_spaces=True
            )
            return result[0]['translation_text']
        except Exception as e:
            logger.error(f"Translation failed: {text} - {e}")
            raise TranslationError(f"Translation error: {str(e)}") from e

# Initialize translator
_translator = NeuralTranslator()

def translate_en_to_tl(text: str) -> str:
    """Public API for translation"""
    return _translator.translate(text)

def quick_translate_en_to_tl(text: str) -> str:
    """Quick utility: Translate English to Tagalog using base MarianMT (no fine-tuning, no caching)"""
    model_name = "Helsinki-NLP/opus-mt-en-tl"
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
    inputs = tokenizer([text], return_tensors="pt", padding=True, truncation=True)
    translated = model.generate(**inputs)
    result = [tokenizer.decode(t, skip_special_tokens=True) for t in translated]
    return result[0] if result else ""

# Example usage for quick testing
if __name__ == "__main__":
    sample_text = "Hello, how are you?"
    print("Quick MarianMT translation:")
    print(f"EN: {sample_text}")
    print(f"TL: {quick_translate_en_to_tl(sample_text)}")
