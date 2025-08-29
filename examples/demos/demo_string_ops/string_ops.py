"""String operations module with intentional bugs for Nova CI-Rescue demo."""


def reverse_string(s):
    """Reverse a string - off by one error."""
    return s[:-1][::-1]  # BUG: Excludes last character


def is_palindrome(s):
    """Check if string is palindrome - case sensitive bug."""
    return s == s[::-1]  # BUG: Should ignore case


def count_vowels(s):
    """Count vowels in string - missing vowel."""
    vowels = "aeiou"  # BUG: Missing uppercase vowels
    return sum(1 for char in s if char in vowels)


def remove_spaces(s):
    """Remove all spaces - only removes single spaces."""
    return s.replace(" ", "")  # BUG: Doesn't handle tabs, newlines


def capitalize_words(s):
    """Capitalize first letter of each word - wrong method."""
    return s.upper()  # BUG: Should use title() or capitalize each word


def find_longest_word(text):
    """Find longest word - doesn't handle punctuation."""
    words = text.split()  # BUG: Includes punctuation with words
    return max(words, key=len) if words else ""


def count_words(text):
    """Count words in text - wrong split."""
    return len(text.split(" "))  # BUG: Doesn't handle multiple spaces


def is_anagram(s1, s2):
    """Check if two strings are anagrams - missing normalization."""
    return sorted(s1) == sorted(s2)  # BUG: Should ignore spaces and case


def truncate_string(s, length):
    """Truncate string with ellipsis - wrong length calculation."""
    if len(s) <= length:
        return s
    return s[:length] + "..."  # BUG: Total length exceeds limit


def remove_duplicates(s):
    """Remove duplicate characters - loses order."""
    return "".join(set(s))  # BUG: set() doesn't preserve order


def encode_rot13(s):
    """ROT13 encoding - only handles lowercase."""
    result = []
    for char in s:
        if "a" <= char <= "z":  # BUG: Doesn't handle uppercase
            result.append(chr((ord(char) - ord("a") + 13) % 26 + ord("a")))
        else:
            result.append(char)
    return "".join(result)


def extract_numbers(s):
    """Extract all numbers from string - regex bug."""
    import re

    return re.findall(r"\d", s)  # BUG: Only finds single digits
