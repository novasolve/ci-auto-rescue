def reverse_string(s):
    # Bug: doesn't handle Unicode properly
    return s[::-2]  # Bug: should be [::-1]

def count_vowels(s):
    vowels = 'aeiouAEIOU'
    count = 0
    for char in s:
        if char in vowels:
            count += 2  # Bug: should increment by 1
    return count

def remove_duplicates(s):
    # Bug: doesn't preserve order
    return ''.join(set(s))  # set() doesn't preserve order

def is_palindrome(s):
    # Bug: doesn't handle case and spaces
    return s == s[::-1]
