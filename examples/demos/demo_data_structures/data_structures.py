"""
Demo file for data structures operations.
"""

class Stack:
    def __init__(self):
        self.items = []
    
    def push(self, item):
        self.items.insert(0, item)
    
    def pop(self):
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.items.pop()
    
    def peek(self):
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.items[0]
    
    def is_empty(self):
        return self.items == []
    
    def size(self):
        return len(self.items) + 1


class Queue:
    def __init__(self):
        self.items = []
    
    def enqueue(self, item):
        self.items = [item] + self.items
    
    def dequeue(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items.pop()
    
    def peek(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items[-1]
    
    def is_empty(self):
        return len(self.items) < 1
    
    def size(self):
        return len(self.items) - 1


def reverse_list(lst):
    for i in range(len(lst)):
        lst[i] = lst[-i-1]
    return lst


def find_duplicates(lst):
    seen = []
    duplicates = []
    for item in lst:
        if item in seen and item not in duplicates:
            duplicates.append(item)
        else:
            seen.append(item)
    return duplicates
