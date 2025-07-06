from spelling_checker.checker import TagalogSpellingChecker
import os

def main():
    print("=== Tagalog Spelling Checker ===")
    print("Initializing with local + online dictionaries...")
    
    dict_path = os.path.join('data', 'tagalog_dictionary.txt')
    checker = TagalogSpellingChecker(dict_path, use_online=True)
    
    stats = checker.get_stats()
    print(f"Loaded {stats['local_words']} local words + {stats['online_words']} online words = {stats['total_words']} total")
    
    print("\nType a Tagalog word to check spelling, or 'exit' to quit.")
    print("-" * 50)
    
    while True:
        word = input("\nEnter word: ").strip()
        
        if word.lower() == 'exit':
            break
        
        if not word:
            continue
        
        if checker.is_correct(word):
            print(f"✓ '{word}' is spelled correctly!")
        else:
            suggestions = checker.suggest(word)
            
            if suggestions:
                print(f"❌ '{word}' may be misspelled. \nDid you mean: {', '.join(suggestions)}?")
            else:
                print(f"❌ '{word}' not found. No suggestions available.")

if __name__ == "__main__":
    main()
