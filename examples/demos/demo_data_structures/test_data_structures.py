"""
Test file for data structures operations.
"""

from data_structures import Stack, Queue, reverse_list, find_duplicates


def test_stack_operations():
    """Test basic stack operations."""
    stack = Stack()
    
    # Test empty stack
    assert stack.is_empty() == True
    assert stack.size() == 0
    
    # Test push
    stack.push(1)
    stack.push(2)
    stack.push(3)
    assert stack.size() == 3
    assert stack.is_empty() == False
    
    # Test peek
    assert stack.peek() == 3
    assert stack.size() == 3  # Peek shouldn't remove item
    
    # Test pop
    assert stack.pop() == 3
    assert stack.pop() == 2
    assert stack.size() == 1
    assert stack.pop() == 1
    assert stack.is_empty() == True


def test_stack_exceptions():
    """Test stack exception handling."""
    stack = Stack()
    
    try:
        stack.pop()
        assert False, "Should raise IndexError"
    except IndexError as e:
        assert str(e) == "Stack is empty"
    
    try:
        stack.peek()
        assert False, "Should raise IndexError"
    except IndexError as e:
        assert str(e) == "Stack is empty"


def test_queue_operations():
    """Test basic queue operations."""
    queue = Queue()
    
    # Test empty queue
    assert queue.is_empty() == True
    assert queue.size() == 0
    
    # Test enqueue
    queue.enqueue(1)
    queue.enqueue(2)
    queue.enqueue(3)
    assert queue.size() == 3
    assert queue.is_empty() == False
    
    # Test peek
    assert queue.peek() == 1
    assert queue.size() == 3  # Peek shouldn't remove item
    
    # Test dequeue
    assert queue.dequeue() == 1
    assert queue.dequeue() == 2
    assert queue.size() == 1
    assert queue.dequeue() == 3
    assert queue.is_empty() == True


def test_queue_exceptions():
    """Test queue exception handling."""
    queue = Queue()
    
    try:
        queue.dequeue()
        assert False, "Should raise IndexError"
    except IndexError as e:
        assert str(e) == "Queue is empty"
    
    try:
        queue.peek()
        assert False, "Should raise IndexError"
    except IndexError as e:
        assert str(e) == "Queue is empty"


def test_reverse_list():
    """Test list reversal."""
    # Test with odd number of elements
    lst1 = [1, 2, 3, 4, 5]
    assert reverse_list(lst1) == [5, 4, 3, 2, 1]
    
    # Test with even number of elements
    lst2 = [1, 2, 3, 4]
    assert reverse_list(lst2) == [4, 3, 2, 1]
    
    # Test with empty list
    lst3 = []
    assert reverse_list(lst3) == []
    
    # Test with single element
    lst4 = [1]
    assert reverse_list(lst4) == [1]


def test_find_duplicates():
    """Test finding duplicates in a list."""
    # Test with duplicates
    lst1 = [1, 2, 3, 2, 4, 3, 5]
    duplicates = find_duplicates(lst1)
    assert set(duplicates) == {2, 3}
    
    # Test without duplicates
    lst2 = [1, 2, 3, 4, 5]
    assert find_duplicates(lst2) == []
    
    # Test with all duplicates
    lst3 = [1, 1, 1, 1]
    duplicates = find_duplicates(lst3)
    assert set(duplicates) == {1}
    
    # Test empty list
    lst4 = []
    assert find_duplicates(lst4) == []
