"""Tests for string utilities module."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from string_utils import StringProcessor


class TestStringProcessor:
    @pytest.fixture
    def processor(self):
        return StringProcessor()
    
    def test_reverse_string(self, processor):
        assert processor.reverse_string("hello") == "olleh"
        assert processor.reverse_string("") == ""
        assert processor.reverse_string("a") == "a"
    
    def test_is_palindrome(self, processor):
        assert processor.is_palindrome("racecar") is True
        assert processor.is_palindrome("A man, a plan, a canal: Panama") is True
        assert processor.is_palindrome("hello") is False
        assert processor.is_palindrome("") is True
    
    def test_count_vowels(self, processor):
        assert processor.count_vowels("hello") == 2
        assert processor.count_vowels("aeiou") == 5
        assert processor.count_vowels("xyz") == 0
        assert processor.count_vowels("") == 0
        assert processor.count_vowels("HELLO") == 2
    
    def test_capitalize_words(self, processor):
        assert processor.capitalize_words("hello world") == "Hello World"
        assert processor.capitalize_words("python is great") == "Python Is Great"
        assert processor.capitalize_words("") == ""
        assert processor.capitalize_words("a") == "A"
    
    def test_remove_duplicates(self, processor):
        assert processor.remove_duplicates("hello") == "helo"
        assert processor.remove_duplicates("aabbcc") == "abc"
        assert processor.remove_duplicates("") == ""
        assert processor.remove_duplicates("a") == "a"
        assert processor.remove_duplicates("abcdef") == "abcdef"
    
    def test_find_longest_word(self, processor):
        assert processor.find_longest_word("The quick brown fox") == "quick"
        assert processor.find_longest_word("Python programming language") == "programming"
        assert processor.find_longest_word("") is None
        assert processor.find_longest_word("a") == "a"
    
    def test_is_valid_email(self, processor):
        assert processor.is_valid_email("test@example.com") is True
        assert processor.is_valid_email("user.name@domain.co.uk") is True
        assert processor.is_valid_email("invalid.email") is False
        assert processor.is_valid_email("@example.com") is False
        assert processor.is_valid_email("test@") is False
    
    def test_truncate_string(self, processor):
        assert processor.truncate_string("Hello world", 5) == "He..."
        assert processor.truncate_string("Short", 10) == "Short"
        assert processor.truncate_string("Truncate this text", 10, ">>") == "Truncate>>"
        
    def test_truncate_string_with_empty_string(self, processor):
        """Test that truncate_string handles empty strings correctly."""
        assert processor.truncate_string("", 5) == ""
        
    def test_truncate_string_zero_length(self, processor):
        """Test that truncate_string raises error for non-positive max_length."""
        with pytest.raises(ValueError, match="max_length must be positive"):
            processor.truncate_string("test", 0)
