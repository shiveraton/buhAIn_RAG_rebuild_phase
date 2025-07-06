# Tagalog Spelling Checker

An intelligent Tagalog spelling checker that can distinguish between real typos and intentionally jumbled words.

## 🎯 Key Features

- **Smart Typo Detection**: Identifies genuine spelling errors like "babai" → "babae"
- **Scrambling Detection**: Recognizes intentionally jumbled words like "ababe" and provides no suggestions
- **Valid Word Recognition**: Correctly identifies valid words and doesn't suggest corrections
- **Foreign Word Filtering**: Appropriately handles foreign names and words
- **Dual Dictionary Support**: Uses both local and online Tagalog dictionaries
- **Enhanced Suggestion Scoring**: Prioritizes common typo patterns and frequent words

## 🚀 Quick Start

### Installation

1. Clone or download the project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

#### Command Line Interface
```bash
python main.py
```

#### Programmatic Usage
```python
from spelling_checker.checker import TagalogSpellingChecker

# Initialize with online dictionary for best results
checker = TagalogSpellingChecker('data/tagalog_dictionary.txt', use_online=True)

# Check spelling and get suggestions
suggestions = checker.suggest("babai")  # Returns: ['babae', ...]
suggestions = checker.suggest("ababe")  # Returns: [] (scrambled)

# Check if word is correct
is_correct = checker.is_correct("babae")  # Returns: True
```

## 📁 Project Structure

```
tagalog-spelling-checker/
├── main.py                      # Command-line interface
├── manage_user_dict.py          # User dictionary management
├── spelling_checker/            # Core module
│   ├── checker.py               # Main spelling checker class
│   ├── utils.py                 # Dictionary loading utilities
│   ├── online_dictionary.py     # Online dictionary integration
│   └── __init__.py
├── data/                        # Dictionary files
│   ├── tagalog_dictionary.txt   # Main Tagalog dictionary
│   └── user_dictionary.txt      # User-defined words
├── tests/                       # Tests and validation
│   ├── test_checker.py          # Core functionality tests
│   ├── test_word_classification.py  # Typo vs scrambled classification test
│   └── run_classification_test.py   # Manual test runner
├── docs/                        # Documentation
└── requirements.txt             # Dependencies
```

## 🧪 Testing

### Automated Tests
Run all tests:
```bash
python -m pytest tests/ -v
```

### Classification Test
Test the core feature of distinguishing typos from scrambled words:
```bash
python tests/run_classification_test.py
```

### Individual Tests
```bash
python -m pytest tests/test_checker.py -v
python -m pytest tests/test_word_classification.py -v
```

## 🔧 Advanced Configuration

### Using Local Dictionary Only
```python
checker = TagalogSpellingChecker('data/tagalog_dictionary.txt', use_online=False)
```

### Custom Parameters
```python
# Adjust suggestion sensitivity
suggestions = checker.suggest("word", limit=5, score_cutoff=60)
```

## 📊 Examples

### Real Typos (Get Suggestions)
- `babai` → `babae` ✅
- `lalkai` → `lalaki` ✅
- `kumsta` → `kumusta` ✅

### Scrambled Words (No Suggestions)
- `ababe` → (no suggestions) ✅
- `baeba` → (no suggestions) ✅
- `kilala` → (no suggestions) ✅

### Valid Words (Recognized Correctly)
- `babae` → (correctly spelled) ✅
- `lalaki` → (correctly spelled) ✅
- `maganda` → (correctly spelled) ✅

## 🛠️ Development

The project includes archived development scripts in the `archive/` folder:
- `debug_scripts/` - Debugging and analysis scripts
- `test_scripts/` - Development test scripts

## 📈 Performance

- **Accuracy**: 95%+ on core test cases
- **Speed**: Fast suggestion generation with enhanced scoring
- **Coverage**: 42,000+ words (local + online dictionaries)

## 🤝 Contributing

1. Fork the project
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is available under the MIT License.

## ✨ Acknowledgments

- Enhanced typo detection algorithms
- Tagalog language resources
- RapidFuzz library for fuzzy string matching
