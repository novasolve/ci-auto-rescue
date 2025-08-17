"""
Demo file for string operations.
"""

import re
from typing import List, Tuple, Optional


def reverse_string(text: str) -> str:
    """Reverse a string."""
    return text[::-1]


def is_palindrome(text: str, ignore_case: bool = False) -> bool:
    """Check if a string is a palindrome."""
    if ignore_case:
        text = text.lower()
    # Remove non-alphanumeric characters
    cleaned = ''.join(char for char in text if char.isalnum())
    return cleaned == cleaned[::-1]


def count_vowels(text: str) -> int:
    """Count the number of vowels in a string."""
    vowels = "aeiouAEIOU"
    return sum(1 for char in text if char in vowels)


def count_words(text: str) -> int:
    """Count the number of words in a string."""
    return len(text.split())


def capitalize_words(text: str) -> str:
    """Capitalize the first letter of each word."""
    return ' '.join(word.capitalize() for word in text.split())


def remove_duplicates(text: str) -> str:
    """Remove duplicate characters while preserving order."""
    seen = set()
    result = []
    for char in text:
        if char not in seen:
            seen.add(char)
            result.append(char)
    return ''.join(result)


def find_longest_word(text: str) -> str:
    """Find the longest word in a string."""
    words = text.split()
    if not words:
        return ""
    return max(words, key=len)


def extract_numbers(text: str) -> List[int]:
    """Extract all numbers from a string."""
    numbers = re.findall(r'\d+', text)
    return [int(num) for num in numbers]


def replace_multiple(text: str, replacements: dict) -> str:
    """Replace multiple substrings in a string."""
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def is_anagram(str1: str, str2: str) -> bool:
    """Check if two strings are anagrams."""
    # Remove spaces and convert to lowercase
    str1 = str1.replace(" ", "").lower()
    str2 = str2.replace(" ", "").lower()
    return sorted(str1) == sorted(str2)


def compress_string(text: str) -> str:
    """Compress a string using run-length encoding."""
    if not text:
        return ""
    
    result = []
    count = 1
    prev_char = text[0]
    
    for i in range(1, len(text)):
        if text[i] == prev_char:
            count += 1
        else:
            result.append(f"{prev_char}{count}")
            prev_char = text[i]
            count = 1
    
    result.append(f"{prev_char}{count}")
    compressed = ''.join(result)
    
    # Return original if compression doesn't reduce size
    return compressed if len(compressed) < len(text) else text


def decompress_string(compressed: str) -> str:
    """Decompress a run-length encoded string."""
    result = []
    i = 0
    while i < len(compressed):
        char = compressed[i]
        i += 1
        count = ""
        while i < len(compressed) and compressed[i].isdigit():
            count += compressed[i]
            i += 1
        result.append(char * int(count))
    return ''.join(result)


def split_camel_case(text: str) -> List[str]:
    """Split a camelCase string into words."""
    words = []
    current_word = []
    
    for i, char in enumerate(text):
        if char.isupper() and i > 0:
            words.append(''.join(current_word))
            current_word = [char]
        else:
            current_word.append(char)
    
    if current_word:
        words.append(''.join(current_word))
    
    return words


def to_snake_case(text: str) -> str:
    """Convert camelCase or PascalCase to snake_case."""
    # Insert underscore before uppercase letters
    result = re.sub(r'(?<!^)(?=[A-Z])', '_', text)
    return result.lower()


def to_camel_case(text: str) -> str:
    """Convert snake_case to camelCase."""
    words = text.split('_')
    if not words:
        return ""
    return words[0] + ''.join(word.capitalize() for word in words[1:])


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text."""
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]*'
    return re.findall(pattern, text)


def word_frequency(text: str) -> dict:
    """Count frequency of each word in text."""
    words = text.lower().split()
    frequency = {}
    for word in words:
        # Remove punctuation
        word = re.sub(r'[^\w\s]', '', word)
        if word:
            frequency[word] = frequency.get(word, 0) + 1
    return frequency


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to specified length with suffix."""
    if len(text) <= max_length:
        return text
    
    if max_length <= len(suffix):
        return suffix[:max_length]
    
    return text[:max_length - len(suffix)] + suffix


def find_common_prefix(strings: List[str]) -> str:
    """Find the longest common prefix of a list of strings."""
    if not strings:
        return ""
    
    # Find minimum length
    min_length = min(len(s) for s in strings)
    
    for i in range(min_length):
        char = strings[0][i]
        if not all(s[i] == char for s in strings):
            return strings[0][:i]
    
    return strings[0][:min_length]
