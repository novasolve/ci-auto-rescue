"""
Demo file for data structures operations.
"""

class Stack:
    """A simple stack implementation."""
    
    def __init__(self):
        self.items = []
    
    def push(self, item):
        """Add an item to the top of the stack."""
        self.items.append(item)
    
    def pop(self):
        """Remove and return the top item from the stack."""
        if not self.is_empty():
            return self.items.pop()
        raise IndexError("Stack is empty")
    
    def peek(self):
        """Return the top item without removing it."""
        if not self.is_empty():
            return self.items[-1]
        raise IndexError("Stack is empty")
    
    def is_empty(self):
        """Check if the stack is empty."""
        return len(self.items) == 0
    
    def size(self):
        """Return the number of items in the stack."""
        return len(self.items)


class Queue:
    """A simple queue implementation."""
    
    def __init__(self):
        self.items = []
    
    def enqueue(self, item):
        """Add an item to the rear of the queue."""
        self.items.append(item)
    
    def dequeue(self):
        """Remove and return the front item from the queue."""
        if not self.is_empty():
            return self.items.pop(0)
        raise IndexError("Queue is empty")
    
    def peek(self):
        """Return the front item without removing it."""
        if not self.is_empty():
            return self.items[0]
        raise IndexError("Queue is empty")
    
    def is_empty(self):
        """Check if the queue is empty."""
        return len(self.items) == 0
    
    def size(self):
        """Return the number of items in the queue."""
        return len(self.items)


def reverse_list(lst):
    """Reverse a list in place."""
    left = 0
    right = len(lst) - 1
    while left < right:
        lst[left], lst[right] = lst[right], lst[left]
        left += 1
        right -= 1
    return lst


def find_duplicates(lst):
    """Find all duplicate values in a list."""
    seen = set()
    duplicates = set()
    for item in lst:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    return list(duplicates)
