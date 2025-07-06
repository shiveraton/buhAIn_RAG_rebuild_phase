#!/usr/bin/env python3
"""
Simple test runner for the word classification functionality.
Run this script to test typo vs scrambled vs valid word detection.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from test_word_classification import run_manual_test

if __name__ == "__main__":
    print("Running Tagalog Spelling Checker - Word Classification Test")
    print("=" * 60)
    
    try:
        success = run_manual_test()
        if success:
            print("\n✅ All classification tests passed!")
        else:
            print("\n❌ Some classification tests failed.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        sys.exit(1)
