"""
Test file for string operations.
"""

import pytest
from string_ops import (
    reverse_string, is_palindrome, count_vowels, count_words,
    capitalize_words, remove_duplicates, find_longest_word,
    extract_numbers, replace_multiple, is_anagram, compress_string,
    decompress_string, split_camel_case, to_snake_case, to_camel_case,
    validate_email, extract_urls, word_frequency, truncate_string,
    find_common_prefix
)


def test_reverse_string():
    """Test string reversal."""
    assert reverse_string("hello") == "olleh"
    assert reverse_string("Python") == "nohtyP"
    assert reverse_string("") == ""
    assert reverse_string("a") == "a"
    assert reverse_string("12345") == "54321"


def test_is_palindrome():
    """Test palindrome checking."""
    assert is_palindrome("racecar") == True
    assert is_palindrome("A man a plan a canal Panama", ignore_case=True) == True
    assert is_palindrome("hello") == False
    assert is_palindrome("") == True
    assert is_palindrome("a") == True
    assert is_palindrome("RaceCar", ignore_case=True) == True
    assert is_palindrome("RaceCar", ignore_case=False) == False


def test_count_vowels():
    """Test vowel counting."""
    assert count_vowels("hello") == 2
    assert count_vowels("Python") == 1
    assert count_vowels("aeiou") == 5
    assert count_vowels("AEIOU") == 5
    assert count_vowels("xyz") == 0
    assert count_vowels("") == 0


def test_count_words():
    """Test word counting."""
    assert count_words("Hello world") == 2
    assert count_words("This is a test") == 4
    assert count_words("") == 0
    assert count_words("   ") == 0
    assert count_words("One") == 1


def test_capitalize_words():
    """Test word capitalization."""
    assert capitalize_words("hello world") == "Hello World"
    assert capitalize_words("python programming") == "Python Programming"
    assert capitalize_words("ALREADY CAPS") == "Already Caps"
    assert capitalize_words("") == ""
    assert capitalize_words("one") == "One"


def test_remove_duplicates():
    """Test duplicate removal."""
    assert remove_duplicates("hello") == "helo"
    assert remove_duplicates("aabbcc") == "abc"
    assert remove_duplicates("abcabc") == "abc"
    assert remove_duplicates("") == ""
    assert remove_duplicates("xyz") == "xyz"


def test_find_longest_word():
    """Test finding longest word."""
    assert find_longest_word("The quick brown fox") == "quick"
    assert find_longest_word("Python programming language") == "programming"
    assert find_longest_word("") == ""
    assert find_longest_word("a") == "a"
    assert find_longest_word("abc def ghi") == "abc"  # First when equal length


def test_extract_numbers():
    """Test number extraction."""
    assert extract_numbers("abc123def456") == [123, 456]
    assert extract_numbers("The price is $42.99") == [42, 99]
    assert extract_numbers("No numbers here") == []
    assert extract_numbers("2024 is the year") == [2024]
    assert extract_numbers("") == []


def test_replace_multiple():
    """Test multiple replacements."""
    replacements = {"hello": "hi", "world": "earth"}
    assert replace_multiple("hello world", replacements) == "hi earth"
    
    replacements2 = {"a": "b", "b": "c"}
    assert replace_multiple("aaa bbb", replacements2) == "ccc ccc"
    
    assert replace_multiple("test", {}) == "test"


def test_is_anagram():
    """Test anagram checking."""
    assert is_anagram("listen", "silent") == True
    assert is_anagram("hello", "world") == False
    assert is_anagram("The Eyes", "They See") == True
    assert is_anagram("", "") == True
    assert is_anagram("a", "a") == True


def test_compress_string():
    """Test string compression."""
    assert compress_string("aabbbcccc") == "a2b3c4"
    assert compress_string("abc") == "abc"  # No compression benefit
    assert compress_string("aabbcc") == "aabbcc"  # No compression benefit
    assert compress_string("") == ""
    assert compress_string("aaaa") == "a4"


def test_decompress_string():
    """Test string decompression."""
    assert decompress_string("a2b3c4") == "aabbbcccc"
    assert decompress_string("a1b1c1") == "abc"
    assert decompress_string("x10") == "x" * 10
    assert decompress_string("") == ""


def test_split_camel_case():
    """Test camelCase splitting."""
    assert split_camel_case("camelCase") == ["camel", "Case"]
    assert split_camel_case("PascalCase") == ["Pascal", "Case"]
    assert split_camel_case("HTTPSConnection") == ["HTTPS", "Connection"]
    assert split_camel_case("simple") == ["simple"]
    assert split_camel_case("") == []


def test_to_snake_case():
    """Test conversion to snake_case."""
    assert to_snake_case("camelCase") == "camel_case"
    assert to_snake_case("PascalCase") == "pascal_case"
    assert to_snake_case("HTTPSConnection") == "https_connection"
    assert to_snake_case("simple") == "simple"
    assert to_snake_case("") == ""


def test_to_camel_case():
    """Test conversion to camelCase."""
    assert to_camel_case("snake_case") == "snakeCase"
    assert to_camel_case("long_snake_case") == "longSnakeCase"
    assert to_camel_case("simple") == "simple"
    assert to_camel_case("") == ""
    assert to_camel_case("_leading") == "Leading"


def test_validate_email():
    """Test email validation."""
    assert validate_email("user@example.com") == True
    assert validate_email("test.user+tag@domain.co.uk") == True
    assert validate_email("invalid.email") == False
    assert validate_email("@example.com") == False
    assert validate_email("user@") == False
    assert validate_email("") == False


def test_extract_urls():
    """Test URL extraction."""
    text = "Visit https://example.com and http://test.org for more info"
    urls = extract_urls(text)
    assert len(urls) == 2
    assert "https://example.com" in urls
    assert "http://test.org" in urls
    
    assert extract_urls("No URLs here") == []
    assert extract_urls("") == []


def test_word_frequency():
    """Test word frequency counting."""
    freq = word_frequency("the cat and the dog")
    assert freq == {"the": 2, "cat": 1, "and": 1, "dog": 1}
    
    freq2 = word_frequency("Hello, hello! HELLO?")
    assert freq2 == {"hello": 3}
    
    assert word_frequency("") == {}


def test_truncate_string():
    """Test string truncation."""
    assert truncate_string("Hello, World!", 10) == "Hello, ..."
    assert truncate_string("Short", 10) == "Short"
    assert truncate_string("Exactly10!", 10) == "Exactly10!"
    assert truncate_string("TooLong", 5, "..") == "Too.."
    assert truncate_string("Hi", 2, "...") == ".."


def test_find_common_prefix():
    """Test finding common prefix."""
    assert find_common_prefix(["flower", "flow", "flight"]) == "fl"
    assert find_common_prefix(["dog", "racecar", "car"]) == ""
    assert find_common_prefix(["interspecies", "interstellar", "interstate"]) == "inters"
    assert find_common_prefix(["same", "same", "same"]) == "same"
    assert find_common_prefix([]) == ""
    assert find_common_prefix(["single"]) == "single"
