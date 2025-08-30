"""Tests for string operations - all will fail due to bugs."""

from string_ops import (
    reverse_string,
    is_palindrome,
    count_vowels,
    remove_spaces,
    capitalize_words,
    find_longest_word,
    count_words,
    is_anagram,
    truncate_string,
    remove_duplicates,
    encode_rot13,
    extract_numbers,
)


def test_reverse_string():
    """Test string reversal."""
    assert reverse_string("hello") == "olleh"
    assert reverse_string("Python") == "nohtyP"
    assert reverse_string("12345") == "54321"
    assert reverse_string("a") == "a"


def test_is_palindrome():
    """Test palindrome checker."""
    assert is_palindrome("racecar")
    assert is_palindrome("A man a plan a canal Panama")
    assert is_palindrome("RaceCar")
    assert not is_palindrome("hello")


def test_count_vowels():
    """Test vowel counting."""
    assert count_vowels("hello") == 2
    assert count_vowels("HELLO") == 2
    assert count_vowels("Python") == 1
    assert count_vowels("AEIOUaeiou") == 10


def test_remove_spaces():
    """Test space removal."""
    assert remove_spaces("hello world") == "helloworld"
    assert remove_spaces("no spaces") == "nospaces"
    assert remove_spaces("tabs\there") == "tabshere"
    assert remove_spaces("new\nline") == "newline"


def test_capitalize_words():
    """Test word capitalization."""
    assert capitalize_words("hello world") == "Hello World"
    assert capitalize_words("python programming") == "Python Programming"
    assert capitalize_words("TEST case") == "Test Case"
    assert capitalize_words("oneword") == "Oneword"


def test_find_longest_word():
    """Test finding longest word."""
    assert find_longest_word("The quick brown fox") == "quick"
    assert find_longest_word("Python programming language") == "programming"
    assert find_longest_word("Hello, world!") == "Hello"
    assert find_longest_word("") == ""


def test_count_words():
    """Test word counting."""
    assert count_words("hello world") == 2
    assert count_words("one two three four") == 4
    assert count_words("multiple   spaces") == 2
    assert count_words("  leading and trailing  ") == 3


def test_is_anagram():
    """Test anagram checker."""
    assert is_anagram("listen", "silent")
    assert is_anagram("Listen", "Silent")
    assert is_anagram("a gentleman", "elegant man")
    assert not is_anagram("hello", "world")


def test_truncate_string():
    """Test string truncation."""
    assert truncate_string("hello", 10) == "hello"
    assert truncate_string("hello world", 8) == "hello..."
    assert len(truncate_string("long string here", 10)) == 10
    assert truncate_string("short", 3) == "..."


def test_remove_duplicates():
    """Test duplicate removal."""
    assert remove_duplicates("hello") == "helo"
    assert remove_duplicates("aabbcc") == "abc"
    assert remove_duplicates("abcabc") == "abc"
    assert list(remove_duplicates("aabbcc")) == ["a", "b", "c"]  # Check order


def test_encode_rot13():
    """Test ROT13 encoding."""
    assert encode_rot13("hello") == "uryyb"
    assert encode_rot13("HELLO") == "URYYB"
    assert encode_rot13("Hello World") == "Uryyb Jbeyq"
    assert encode_rot13(encode_rot13("test")) == "test"


def test_extract_numbers():
    """Test number extraction."""
    assert extract_numbers("abc123def456") == ["123", "456"]
    assert extract_numbers("phone: 555-1234") == ["555", "1234"]
    assert extract_numbers("price: $19.99") == ["19", "99"]
    assert extract_numbers("no numbers here") == []
