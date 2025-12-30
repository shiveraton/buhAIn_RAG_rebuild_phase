"""Quick debug test"""
import re

filipino_corrections = {
    r'\bdo mate yo\b': 'doon sa',
    r'\bpila fo\b': 'pilipino',
}

text = "test do mate yo test"
for pattern, replacement in filipino_corrections.items():
    print(f"Pattern: {pattern}, Replacement: {replacement}")
    matches = len(re.findall(pattern, text, re.IGNORECASE))
    print(f"Matches: {matches}")
    text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    print(f"Result: {text}")
