import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from string_utils import reverse_string, count_vowels, remove_duplicates, is_palindrome
import pytest

def test_reverse_string():
    assert reverse_string("hello") == "olleh"
    assert reverse_string("Python") == "nohtyP"
    assert reverse_string("") == ""
    
def test_count_vowels():
    assert count_vowels("hello") == 2
    assert count_vowels("Python") == 1
    assert count_vowels("aeiou") == 5
    assert count_vowels("xyz") == 0
    
def test_remove_duplicates():
    assert remove_duplicates("hello") == "helo"
    assert remove_duplicates("aabbcc") == "abc"
    # Order should be preserved
    assert remove_duplicates("abcabc") == "abc"
