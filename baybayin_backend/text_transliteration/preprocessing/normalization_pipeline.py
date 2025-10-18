from text_transliteration.helper.regex_utils import remove_numbers;
from .text_cleaning import remove_special_characters, substitute_foreign_letters_to_native;

def text_transliteration_normalization(text, transliterate):
    warnings = []
    norm_text = text.lower()

    norm_text, removed_num = remove_numbers(norm_text)
    if removed_num:
        warnings.append(f"Removed numbers: {' '.join(removed_num)}")
        
    norm_text, removed_special_char = remove_special_characters(norm_text)
    if removed_special_char:
        warnings.append(f"Removed special characters: {' '.join(removed_special_char)}")
        
    if transliterate == "to_baybayin":
        norm_text, substitutions = substitute_foreign_letters_to_native(norm_text)
        if substitutions:
            warnings.append(f"Substituted foreign letters: {' '.join(substitutions)}")
        
    return norm_text, warnings
    