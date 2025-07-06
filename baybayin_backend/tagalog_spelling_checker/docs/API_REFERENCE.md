# API Reference

## TagalogSpellingChecker

The main class for Tagalog spelling checking functionality.

### Constructor

```python
TagalogSpellingChecker(dict_path, use_online=False)
```

**Parameters:**
- `dict_path` (str): Path to the local dictionary file
- `use_online` (bool): Whether to use online dictionary (default: False)

**Example:**
```python
checker = TagalogSpellingChecker('data/tagalog_dictionary.txt', use_online=True)
```

### Methods

#### `suggest(word, limit=3, score_cutoff=70)`

Get spelling suggestions for a word.

**Parameters:**
- `word` (str): The word to check
- `limit` (int): Maximum number of suggestions (default: 3)
- `score_cutoff` (int): Minimum similarity score (default: 70)

**Returns:**
- `list`: List of suggested corrections, or empty list if no suggestions

**Example:**
```python
suggestions = checker.suggest("babai")  # ['babae', 'babag', 'babad']
suggestions = checker.suggest("ababe")  # [] (scrambled word)
```

#### `is_correct(word)`

Check if a word is spelled correctly.

**Parameters:**
- `word` (str): The word to check

**Returns:**
- `bool`: True if word is in dictionary, False otherwise

**Example:**
```python
is_correct = checker.is_correct("babae")  # True
is_correct = checker.is_correct("babai")  # False
```

#### `get_stats()`

Get statistics about the loaded dictionaries.

**Returns:**
- `dict`: Dictionary with statistics including:
  - `local_words`: Number of local dictionary words
  - `online_words`: Number of online dictionary words
  - `total_words`: Total number of words
  - `online_enabled`: Whether online dictionary is enabled

**Example:**
```python
stats = checker.get_stats()
print(f"Total words: {stats['total_words']}")
```

## Behavior Guidelines

### Suggestion Logic

The checker uses intelligent logic to determine when to provide suggestions:

1. **Valid Words**: No suggestions returned
   ```python
   checker.suggest("babae")  # [] (correct word)
   ```

2. **Real Typos**: Suggestions provided
   ```python
   checker.suggest("babai")  # ['babae', ...] (typo)
   ```

3. **Scrambled Words**: No suggestions (detected as intentional)
   ```python
   checker.suggest("ababe")  # [] (scrambled)
   ```

4. **Foreign Words**: No suggestions
   ```python
   checker.suggest("JavaScript")  # [] (foreign)
   ```

### Scoring Algorithm

The suggestion scoring prioritizes:

1. **End character substitution** (+30 points) - e.g., "babai" → "babae"
2. **Beginning character substitution** (+25 points)
3. **Single character errors** (+20 points)
4. **Keyboard proximity** (+18 points)
5. **Adjacent character swaps** (+15 points)
6. **Word frequency** (up to +8 points)
7. **Important/common words** (+20 points)

### Word Type Analysis

The checker classifies input words as:

- **`typo`**: Genuine spelling errors that should get suggestions
- **`scrambled`**: Intentionally jumbled words (no suggestions)
- **`foreign`**: Non-Tagalog words (no suggestions)
- **`valid`**: Correctly spelled words (no suggestions)

## Error Handling

The checker gracefully handles:

- Missing dictionary files
- Network issues (for online dictionary)
- Invalid input characters
- Empty or whitespace-only input

## Thread Safety

The TagalogSpellingChecker class is thread-safe for read operations (checking and suggesting). Dictionary loading should be done in a single thread.
