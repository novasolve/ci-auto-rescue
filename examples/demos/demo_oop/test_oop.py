"""
Test file for object-oriented programming concepts.
"""

import pytest
from oop import (
    Dog, Cat, Bird, BankAccount, Rectangle, Circle,
    Employee, Manager
)


def test_dog_class():
    """Test Dog class functionality."""
    dog = Dog("Buddy", 3, "Golden Retriever")
    
    assert dog.name == "Buddy"
    assert dog.age == 3
    assert dog.breed == "Golden Retriever"
    
    assert dog.make_sound() == "Woof!"
    assert dog.move() == "runs on four legs"
    assert dog.fetch("ball") == "Buddy fetches the ball"
    assert dog.describe() == "Buddy is a 3 year old Dog"


def test_cat_class():
    """Test Cat class functionality."""
    cat = Cat("Whiskers", 5, indoor=True)
    
    assert cat.name == "Whiskers"
    assert cat.age == 5
    assert cat.indoor == True
    
    assert cat.make_sound() == "Meow!"
    assert cat.move() == "walks gracefully"
    assert cat.scratch("furniture") == "Whiskers scratches the furniture"
    assert cat.describe() == "Whiskers is a 5 year old Cat"


def test_bird_class():
    """Test Bird class functionality."""
    # Flying bird
    eagle = Bird("Eagle", 2, can_fly=True)
    assert eagle.move() == "flies through the air"
    assert eagle.make_sound() == "Tweet!"
    
    # Non-flying bird
    penguin = Bird("Penguin", 4, can_fly=False)
    assert penguin.move() == "walks on two legs"


def test_bank_account():
    """Test BankAccount class with encapsulation."""
    account = BankAccount("123456", 1000)
    
    # Test properties
    assert account.balance == 1000
    assert account.account_number == "123456"
    
    # Test deposit
    assert account.deposit(500) == 1500
    assert account.balance == 1500
    
    # Test withdraw
    assert account.withdraw(200) == 1300
    assert account.balance == 1300
    
    # Test transaction history
    history = account.get_transaction_history()
    assert len(history) == 2
    assert "Deposited: $500.00" in history
    assert "Withdrew: $200.00" in history


def test_bank_account_exceptions():
    """Test BankAccount exception handling."""
    account = BankAccount("123456", 100)
    
    # Test invalid deposit
    with pytest.raises(ValueError) as exc_info:
        account.deposit(-50)
    assert "Deposit amount must be positive" in str(exc_info.value)
    
    # Test invalid withdrawal
    with pytest.raises(ValueError) as exc_info:
        account.withdraw(-50)
    assert "Withdrawal amount must be positive" in str(exc_info.value)
    
    # Test insufficient funds
    with pytest.raises(ValueError) as exc_info:
        account.withdraw(200)
    assert "Insufficient funds" in str(exc_info.value)


def test_rectangle_shape():
    """Test Rectangle class."""
    rect = Rectangle(10, 5)
    
    assert rect.width == 10
    assert rect.height == 5
    assert rect.area() == 50
    assert rect.perimeter() == 30


def test_circle_shape():
    """Test Circle class."""
    circle = Circle(5)
    
    assert circle.radius == 5
    assert abs(circle.area() - 78.53975) < 0.0001
    assert abs(circle.perimeter() - 31.4159) < 0.0001


def test_employee_class():
    """Test Employee class with class variables and methods."""
    # Reset employee count for testing
    Employee._employee_count = 0
    
    emp1 = Employee("John Doe", "EMP001", 50000)
    emp2 = Employee("Jane Smith", "EMP002", 60000)
    
    # Test instance attributes
    assert emp1.name == "John Doe"
    assert emp1.employee_id == "EMP001"
    assert emp1.get_salary() == 50000
    
    # Test class variables
    assert Employee.company_name == "Tech Corp"
    assert Employee.get_employee_count() == 2
    
    # Test static method
    assert Employee.is_valid_id("EMP001") == True
    assert Employee.is_valid_id("123456") == True
    assert Employee.is_valid_id("EMP") == False
    assert Employee.is_valid_id("EMP00!") == False
    
    # Test give_raise
    assert abs(emp1.give_raise(10) - 55000) < 0.01
    assert abs(emp1.get_salary() - 55000) < 0.01


def test_employee_raise_exception():
    """Test Employee raise exception."""
    emp = Employee("Test", "TST001", 50000)
    
    with pytest.raises(ValueError) as exc_info:
        emp.give_raise(-10)
    assert "Raise percentage cannot be negative" in str(exc_info.value)


def test_manager_class():
    """Test Manager class with inheritance."""
    manager = Manager("Boss", "MGR001", 80000)
    emp1 = Employee("Worker1", "EMP001", 40000)
    emp2 = Employee("Worker2", "EMP002", 45000)
    
    # Test inheritance
    assert manager.name == "Boss"
    assert manager.get_salary() == 80000
    
    # Test team management
    assert manager.get_team_size() == 0
    
    manager.add_team_member(emp1)
    manager.add_team_member(emp2)
    assert manager.get_team_size() == 2
    
    # Test duplicate addition
    manager.add_team_member(emp1)
    assert manager.get_team_size() == 2
    
    # Test removal
    assert manager.remove_team_member(emp1) == True
    assert manager.get_team_size() == 1
    
    # Test removing non-existent member
    assert manager.remove_team_member(emp1) == False
    assert manager.get_team_size() == 1


def test_polymorphism():
    """Test polymorphic behavior with animals."""
    animals = [
        Dog("Rex", 4, "Labrador"),
        Cat("Mittens", 2, indoor=False),
        Bird("Tweety", 1, can_fly=True)
    ]
    
    sounds = [animal.make_sound() for animal in animals]
    assert sounds == ["Woof!", "Meow!", "Tweet!"]
    
    movements = [animal.move() for animal in animals]
    assert movements == ["runs on four legs", "walks gracefully", "flies through the air"]