"""String utilities module for demonstrating Nova CI-Rescue."""

import re
from typing import List, Optional


class StringProcessor:
    """String processing utilities."""

    def reverse_string(self, text: str) -> str:
        """Reverse a string."""
        return text[::-1]

    def is_palindrome(self, text: str) -> bool:
        """Check if a string is a palindrome (case-insensitive)."""
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
        return cleaned == cleaned[::-1]

    def count_vowels(self, text: str) -> int:
        """Count the number of vowels in a string."""
        vowels = 'aeiouAEIOU'
        return sum(1 for char in text if char in vowels)

    def capitalize_words(self, text: str) -> str:
        """Capitalize the first letter of each word."""
        return ' '.join(word.capitalize() for word in text.split())

    def remove_duplicates(self, text: str) -> str:
        """Remove consecutive duplicate characters."""
        if not text:
            return text

        result = [text[0]]
        for char in text[1:]:
            if char != result[-1]:
                result.append(char)
        return ''.join(result)

    def find_longest_word(self, text: str) -> Optional[str]:
        """Find the longest word in a string."""
        words = text.split()
        if not words:
            return None
        return max(words, key=len)

    def is_valid_email(self, email: str) -> bool:
        """Check if a string is a valid email address."""
        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def truncate_string(self, text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate a string to a maximum length."""
        if max_length <= 0:
            raise ValueError("max_length must be positive")
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
