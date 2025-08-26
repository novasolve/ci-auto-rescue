"""Object-oriented programming module with intentional bugs for Nova CI-Rescue demo."""

class BankAccount:
    """Bank account with bugs."""
    def __init__(self, balance=0):
        self.balance = balance  # BUG: Should be private (_balance)
    
    def deposit(self, amount):
        """Deposit money - no validation."""
        self.balance += amount  # BUG: No negative amount check
    
    def withdraw(self, amount):
        """Withdraw money - no balance check."""
        self.balance -= amount  # BUG: Allows negative balance
        return amount
    
    def get_balance(self):
        """Get balance - wrong value."""
        return self.balance * 100  # BUG: Returns cents instead of dollars

class Rectangle:
    """Rectangle class with bugs."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    def area(self):
        """Calculate area - wrong formula."""
        return self.width + self.height  # BUG: Should multiply
    
    def perimeter(self):
        """Calculate perimeter - wrong formula."""
        return self.width * self.height  # BUG: Should be 2*(w+h)
    
    def is_square(self):
        """Check if square - inverted logic."""
        return self.width != self.height  # BUG: Should use ==

class Employee:
    """Employee class with bugs."""
    def __init__(self, name, salary):
        self.name = name
        self.salary = salary
        self.bonuses = []
    
    def add_bonus(self, amount):
        """Add bonus - modifies wrong list."""
        self.bonuses = amount  # BUG: Should append to list
    
    def total_compensation(self):
        """Calculate total - wrong calculation."""
        return self.salary + len(self.bonuses)  # BUG: Should sum bonuses
    
    def give_raise(self, percentage):
        """Give raise - wrong calculation."""
        self.salary += percentage  # BUG: Should multiply by (1 + percentage/100)

class Animal:
    """Base animal class."""
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        """Make sound - no implementation."""
        pass  # BUG: Should raise NotImplementedError

class Dog(Animal):
    """Dog class with inheritance bugs."""
    def __init__(self, name, breed):
        self.name = name  # BUG: Should call super().__init__
        self.breed = breed
    
    def speak(self):
        """Dog sound - wrong output."""
        return "Meow"  # BUG: Dogs don't meow

class Cat(Animal):
    """Cat class with inheritance bugs."""
    def __init__(self, name):
        # BUG: Forgot to call super().__init__
        self.color = "black"  # BUG: Lost name attribute

class ShoppingCart:
    """Shopping cart with bugs."""
    def __init__(self):
        self.items = {}
    
    def add_item(self, item, quantity=1):
        """Add item - overwrites quantity."""
        self.items[item] = quantity  # BUG: Should increment if exists
    
    def remove_item(self, item):
        """Remove item - no existence check."""
        del self.items[item]  # BUG: KeyError if not exists
    
    def total_items(self):
        """Count total items - counts unique items."""
        return len(self.items)  # BUG: Should sum quantities

class EmailValidator:
    """Email validator with bugs."""
    @staticmethod
    def is_valid(email):
        """Validate email - incomplete check."""
        return "@" in email  # BUG: Too simple validation
    
    @classmethod
    def normalize(cls, email):
        """Normalize email - wrong method."""
        return email.upper()  # BUG: Should use lower()

class Temperature:
    """Temperature converter with bugs."""
    def __init__(self, celsius):
        self.celsius = celsius
    
    @property
    def fahrenheit(self):
        """Convert to Fahrenheit - wrong formula."""
        return self.celsius * 2 + 32  # BUG: Should be *9/5 + 32
    
    @fahrenheit.setter
    def fahrenheit(self, value):
        """Set via Fahrenheit - wrong formula."""
        self.celsius = (value - 32) / 2  # BUG: Should be /9*5
