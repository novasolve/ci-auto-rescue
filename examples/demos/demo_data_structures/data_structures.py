"""Data structures module with intentional bugs for Nova CI-Rescue demo."""


class Stack:
    """Stack implementation with bugs."""

    def __init__(self):
        self.items = []

    def push(self, item):
        """Push item to stack - adds to beginning instead of end."""
        self.items.insert(0, item)  # BUG: Should append to end

    def pop(self):
        """Pop item from stack - no empty check."""
        return self.items.pop()  # BUG: No IndexError protection

    def peek(self):
        """Peek at top item - wrong index."""
        return self.items[0]  # BUG: Should be [-1]

    def is_empty(self):
        """Check if stack is empty - inverted logic."""
        return len(self.items) > 0  # BUG: Should be == 0


class Queue:
    """Queue implementation with bugs."""

    def __init__(self):
        self.items = []

    def enqueue(self, item):
        """Add item to queue - wrong end."""
        self.items.append(item)  # Correct

    def dequeue(self):
        """Remove item from queue - wrong end."""
        return self.items.pop()  # BUG: Should pop(0)

    def size(self):
        """Get queue size - off by one."""
        return len(self.items) + 1  # BUG: Should not add 1


class LinkedListNode:
    """Node for linked list."""

    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedList:
    """Linked list with bugs."""

    def __init__(self):
        self.head = None

    def append(self, data):
        """Append to list - doesn't handle empty list."""
        new_node = LinkedListNode(data)
        current = self.head
        while current.next:  # BUG: Fails if head is None
            current = current.next
        current.next = new_node

    def prepend(self, data):
        """Prepend to list - doesn't update head."""
        new_node = LinkedListNode(data)
        new_node.next = self.head  # BUG: Doesn't set self.head = new_node

    def find(self, data):
        """Find data in list - wrong comparison."""
        current = self.head
        while current:
            if current == data:  # BUG: Should be current.data == data
                return True
            current = current.next
        return False


def binary_search(arr, target):
    """Binary search with bugs."""
    left, right = 0, len(arr)  # BUG: Should be len(arr) - 1

    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid  # BUG: Should be mid + 1
        else:
            right = mid  # BUG: Should be mid - 1

    return -1


def merge_sort(arr):
    """Merge sort with bugs."""
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    # Merge with bug
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            # BUG: Forgot to increment j

    result.extend(left[i:])
    result.extend(right[j:])
    return result


def find_duplicates(arr):
    """Find duplicates in array - wrong logic."""
    seen = set()
    duplicates = []

    for item in arr:
        if item in seen:
            seen.add(item)  # BUG: Should add to duplicates
        else:
            seen.add(item)

    return duplicates  # BUG: Always returns empty list
