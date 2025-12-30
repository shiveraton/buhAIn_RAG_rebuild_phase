# Trivia Question Repetition Fix

## Problem Summary

The Baybayin trivia question **"What does the Baybayin script 'ᜊ' represent?"** (Answer: "Ba") was appearing repeatedly during gameplay, causing a poor user experience.

### Answer to Your Question
**"ᜊ" represents "Ba"** - it's the Baybayin character for the /ba/ sound.

## Root Causes Identified

### 1. **Single Hardcoded Fallback Question**
```python
# OLD CODE (Line 167 in views.py)
except Exception as e:
    trivia = {
        'question': 'What does the Baybayin script "ᜊ" represent?',
        'options': ['Ba', 'Ka', 'Da', 'Ga'],
        'answer': 'Ba'
    }
```

When RAG (Retrieval-Augmented Generation) failed to generate a question, the system **always** fell back to the same hardcoded question about "ᜊ".

### 2. **Hardcoded Questions Violated Thesis Requirements**
All content should come directly from the PDF source material, not from hardcoded data. This was a critical requirement that was being violated in the fallback scenario.

### 3. **Fallback Bypassed All Diversity Checks**
The recent question tracking mechanism (`recent_questions` list) only worked for successfully generated questions. When an exception occurred, the fallback was used immediately without checking if it was recently asked.

## Solution Implemented

### 1. **PDF-Based Fallback Generation**
Replaced hardcoded questions with a function that generates questions directly from PDF-sourced content:

```python
def get_fallback_question_from_pdf(recent_questions=None, user_profile=None):
    """
    Generate a fallback question directly from PDF-sourced facts.
    This ensures all questions come from the actual PDF content, not hardcoded data.
    """
    # Get fact from PDF database
    if user_profile:
        fact = get_adaptive_fact(user_profile, use_pdf=True)
    else:
        fact = random.choice(PDFCodexEntry.objects.all())
    
    # Check against recent questions
    fact_hash = hash(fact.text[:50])
    if fact_hash in recent_questions:
        # Try another fact
        continue
    
    # Generate question from PDF fact
    trivia = generate_trivia_from_fact(fact)
    return trivia
```

### 2. **Maintained Recent Question Tracking**
The PDF-based fallback respects the `recent_questions` tracking:
- Tries up to 10 different PDF facts
- Skips recently used facts
- Ensures variety from actual source material

### 3. **Updated Both Guest and Authenticated Flows**

**Guest Users (Unauthenticated):**
```python
except Exception as e:
    trivia = get_fallback_question_from_pdf(recent_questions)
    if not trivia:
        return Response({'error': 'Unable to generate trivia'}, status=500)
```

**Authenticated Users:**
```python
except Exception as e:
    try:
        # Try fact-based fallback first
        fact = get_adaptive_fact(profile) or get_random_fact()
        trivia = generate_trivia_from_fact(fact)
    except Exception as inner_e:
        # Final fallback: use PDF-based generation
        trivia = get_fallback_question_from_pdf(recent_questions, profile)
```

## How It Prevents Repetition

1. **PDF Source Variety**: Questions generated from entire PDF database (potentially hundreds/thousands of facts)
2. **Recent Tracking**: Checks against last 10 recently asked questions
3. **Multiple Attempts**: Tries up to 10 different facts before giving up
4. **Adaptive Selection**: Can prioritize user weaknesses when profile available
5. **No Hardcoded Content**: All questions come directly from PDF source material

## Testing Recommendations

1. **Force RAG Failures**: Temporarily disable the RAG API to test fallback behavior
2. **Monitor Logs**: Look for these messages:
   - `"Generated fallback from PDF fact: ..."`
   - `"Skipping recently used fact (attempt X)"`
   - `"All PDF fallback attempts failed"`
3. **User Experience**: Play 10+ games and verify no question repeats within the same session
4. **Verify PDF Content**: Ensure PDF database is populated with sufficient entries
5. **Test Error Handling**: Verify graceful degradation when PDF database is empty

## Files Modified

- **`baybayin_backend/game_seg_trivia/views.py`**
  - Added `get_fallback_question_from_pdf()` function (line ~54)
  - Updated guest user exception handler (line ~233-242)
  - Updated authenticated user exception handler (line ~341-350)

## Why This Matters

This fix directly addresses **critical thesis requirements** by ensuring:
- ✅ **All content comes from PDF source material** - No hardcoded questions
- ✅ **Traceability to source** - Every question linked to a PDF fact
- ✅ **Varied educational content** - Questions pulled from entire PDF database
- ✅ **Graceful degradation** - System handles failures without breaking user experience
- ✅ **Academic integrity** - Content remains verifiable and sourced from research materials

## Key Architectural Principle

**Single Source of Truth**: The PDF database (`PDFCodexEntry`) is now the **exclusive** source for all trivia content, including fallbacks. This ensures:
- Content accuracy and verifiability
- Thesis requirement compliance
- Easier content updates (just update PDF, no code changes)
- Better tracking and analytics (all questions traceable to source)

## Future Improvements

1. **Cache Popular Facts**: Pre-generate questions from frequently used PDF facts
2. **Quality Scoring**: Rank PDF facts by question-generation quality
3. **Analytics**: Track which PDF sections generate the most engaging questions
4. **Difficulty Categorization**: Tag PDF facts by difficulty for better adaptive learning
