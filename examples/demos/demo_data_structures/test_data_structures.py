"""Tests for data structures - all will fail due to bugs."""

import pytest
from data_structures import (
    Stack, Queue, LinkedList, binary_search, merge_sort, find_duplicates
)

class TestStack:
    """Test Stack implementation."""

    def test_push_pop(self):
        """Test push and pop operations."""
        stack = Stack()
        stack.push(1)
        stack.push(2)
        stack.push(3)
        assert stack.pop() == 3
        assert stack.pop() == 2
        assert stack.pop() == 1

    def test_peek(self):
        """Test peek operation."""
        stack = Stack()
        stack.push(1)
        stack.push(2)
        assert stack.peek() == 2
        assert stack.peek() == 2  # Should not remove

    def test_is_empty(self):
        """Test empty check."""
        stack = Stack()
        assert stack.is_empty() == True
        stack.push(1)
        assert stack.is_empty() == False

    def test_pop_empty(self):
        """Test pop on empty stack."""
        stack = Stack()
        with pytest.raises(IndexError):
            stack.pop()

class TestQueue:
    """Test Queue implementation."""

    def test_enqueue_dequeue(self):
        """Test enqueue and dequeue operations."""
        queue = Queue()
        queue.enqueue(1)
        queue.enqueue(2)
        queue.enqueue(3)
        assert queue.dequeue() == 1  # FIFO
        assert queue.dequeue() == 2
        assert queue.dequeue() == 3

    def test_size(self):
        """Test size method."""
        queue = Queue()
        assert queue.size() == 0
        queue.enqueue(1)
        assert queue.size() == 1
        queue.enqueue(2)
        assert queue.size() == 2

class TestLinkedList:
    """Test LinkedList implementation."""

    def test_append(self):
        """Test append operation."""
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        ll.append(3)
        assert ll.find(1) == True
        assert ll.find(2) == True
        assert ll.find(3) == True

    def test_prepend(self):
        """Test prepend operation."""
        ll = LinkedList()
        ll.prepend(1)
        ll.prepend(2)
        assert ll.head.data == 2
        assert ll.head.next.data == 1

    def test_find(self):
        """Test find operation."""
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        assert ll.find(1) == True
        assert ll.find(2) == True
        assert ll.find(3) == False

def test_binary_search():
    """Test binary search."""
    arr = [1, 3, 5, 7, 9, 11, 13]
    assert binary_search(arr, 7) == 3
    assert binary_search(arr, 1) == 0
    assert binary_search(arr, 13) == 6
    assert binary_search(arr, 4) == -1

def test_merge_sort():
    """Test merge sort."""
    assert merge_sort([3, 1, 4, 1, 5, 9]) == [1, 1, 3, 4, 5, 9]
    assert merge_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
    assert merge_sort([1]) == [1]
    assert merge_sort([]) == []

def test_find_duplicates():
    """Test finding duplicates."""
    assert set(find_duplicates([1, 2, 3, 2, 4, 3])) == {2, 3}
    assert find_duplicates([1, 2, 3, 4, 5]) == []
    assert find_duplicates([1, 1, 1, 1]) == [1, 1, 1]  # All but first
    assert find_duplicates([]) == []