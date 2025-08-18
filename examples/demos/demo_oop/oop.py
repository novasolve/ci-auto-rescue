"""
Demo file for object-oriented programming concepts.
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class Animal(ABC):
    """Abstract base class for animals."""
    
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
    
    @abstractmethod
    def make_sound(self) -> str:
        """Make a sound specific to the animal."""
        pass
    
    @abstractmethod
    def move(self) -> str:
        """Describe how the animal moves."""
        pass
    
    def describe(self) -> str:
        """Describe the animal."""
        # Bug: off by one error
        return f"{self.name} is a {self.age + 1} year old {self.__class__.__name__}"


class Dog(Animal):
    """Dog class inheriting from Animal."""
    
    def __init__(self, name: str, age: int, breed: str):
        super().__init__(name, age)
        self.breed = breed
    
    def make_sound(self) -> str:
        # Bug: dogs don't meow
        return "Meow!"
    
    def move(self) -> str:
        # Bug: wrong movement description
        return "flies through the air"
    
    def fetch(self, item: str) -> str:
        """Dog-specific method."""
        return f"{self.name} fetches the {item}"


class Cat(Animal):
    """Cat class inheriting from Animal."""
    
    def __init__(self, name: str, age: int, indoor: bool = True):
        super().__init__(name, age)
        self.indoor = indoor
    
    def make_sound(self) -> str:
        return "Meow!"
    
    def move(self) -> str:
        return "walks gracefully"
    
    def scratch(self, target: str) -> str:
        """Cat-specific method."""
        return f"{self.name} scratches the {target}"


class Bird(Animal):
    """Bird class inheriting from Animal."""
    
    def __init__(self, name: str, age: int, can_fly: bool = True):
        super().__init__(name, age)
        self.can_fly = can_fly
    
    def make_sound(self) -> str:
        return "Tweet!"
    
    def move(self) -> str:
        if self.can_fly:
            return "flies through the air"
        return "walks on two legs"


class BankAccount:
    """Class demonstrating encapsulation and property decorators."""
    
    def __init__(self, account_number: str, initial_balance: float = 0):
        self._account_number = account_number
        self._balance = initial_balance
        self._transaction_history = []
    
    @property
    def balance(self) -> float:
        """Get current balance (read-only property)."""
        return self._balance
    
    @property
    def account_number(self) -> str:
        """Get account number (read-only property)."""
        return self._account_number
    
    def deposit(self, amount: float) -> float:
        """Deposit money into the account."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self._balance += amount
        self._transaction_history.append(f"Deposited: ${amount:.2f}")
        return self._balance
    
    def withdraw(self, amount: float) -> float:
        """Withdraw money from the account."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount
        self._transaction_history.append(f"Withdrew: ${amount:.2f}")
        return self._balance
    
    def get_transaction_history(self) -> List[str]:
        """Get copy of transaction history."""
        return self._transaction_history.copy()


class Shape(ABC):
    """Abstract base class for shapes."""
    
    @abstractmethod
    def area(self) -> float:
        """Calculate area of the shape."""
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        """Calculate perimeter of the shape."""
        pass


class Rectangle(Shape):
    """Rectangle class implementing Shape interface."""
    
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
    
    def area(self) -> float:
        return self.width * self.height
    
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)


class Circle(Shape):
    """Circle class implementing Shape interface."""
    
    def __init__(self, radius: float):
        self.radius = radius
    
    def area(self) -> float:
        return 3.14159 * self.radius ** 2
    
    def perimeter(self) -> float:
        return 2 * 3.14159 * self.radius


class Employee:
    """Base class for employees demonstrating class variables."""
    
    _employee_count = 0
    company_name = "Tech Corp"
    
    def __init__(self, name: str, employee_id: str, salary: float):
        self.name = name
        self.employee_id = employee_id
        self._salary = salary
        Employee._employee_count += 1
    
    @classmethod
    def get_employee_count(cls) -> int:
        """Get total number of employees."""
        return cls._employee_count
    
    @staticmethod
    def is_valid_id(employee_id: str) -> bool:
        """Validate employee ID format."""
        return len(employee_id) == 6 and employee_id.isalnum()
    
    def get_salary(self) -> float:
        """Get employee salary."""
        return self._salary
    
    def give_raise(self, percentage: float) -> float:
        """Give employee a raise."""
        if percentage < 0:
            raise ValueError("Raise percentage cannot be negative")
        self._salary *= (1 + percentage / 100)
        return self._salary


class Manager(Employee):
    """Manager class inheriting from Employee."""
    
    def __init__(self, name: str, employee_id: str, salary: float):
        super().__init__(name, employee_id, salary)
        self.team_members: List[Employee] = []
    
    def add_team_member(self, employee: Employee) -> None:
        """Add employee to manager's team."""
        if employee not in self.team_members:
            self.team_members.append(employee)
    
    def remove_team_member(self, employee: Employee) -> bool:
        """Remove employee from manager's team."""
        if employee in self.team_members:
            self.team_members.remove(employee)
            return True
        return False
    
    def get_team_size(self) -> int:
        """Get number of team members."""
        return len(self.team_members)