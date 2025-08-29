"""Tests for OOP classes - all will fail due to bugs."""

import pytest
from oop_classes import (
    BankAccount,
    Rectangle,
    Employee,
    Animal,
    Dog,
    Cat,
    ShoppingCart,
    EmailValidator,
    Temperature,
)


class TestBankAccount:
    """Test BankAccount class."""

    def test_deposit_withdraw(self):
        """Test deposit and withdraw."""
        account = BankAccount(100)
        account.deposit(50)
        assert account.get_balance() == 150

        account.withdraw(30)
        assert account.get_balance() == 120

    def test_negative_deposit(self):
        """Test negative deposit protection."""
        account = BankAccount(100)
        account.deposit(-50)
        assert account.get_balance() == 100  # Should not change

    def test_overdraft_protection(self):
        """Test overdraft protection."""
        account = BankAccount(100)
        result = account.withdraw(150)
        assert result == 0  # Should not allow
        assert account.get_balance() == 100  # Balance unchanged


class TestRectangle:
    """Test Rectangle class."""

    def test_area(self):
        """Test area calculation."""
        rect = Rectangle(4, 5)
        assert rect.area() == 20

        square = Rectangle(3, 3)
        assert square.area() == 9

    def test_perimeter(self):
        """Test perimeter calculation."""
        rect = Rectangle(4, 5)
        assert rect.perimeter() == 18

        square = Rectangle(3, 3)
        assert square.perimeter() == 12

    def test_is_square(self):
        """Test square detection."""
        rect = Rectangle(4, 5)
        assert rect.is_square() == False

        square = Rectangle(3, 3)
        assert square.is_square() == True


class TestEmployee:
    """Test Employee class."""

    def test_bonuses(self):
        """Test bonus handling."""
        emp = Employee("John", 50000)
        emp.add_bonus(1000)
        emp.add_bonus(2000)

        assert len(emp.bonuses) == 2
        assert emp.total_compensation() == 53000

    def test_raise(self):
        """Test salary raise."""
        emp = Employee("Jane", 60000)
        emp.give_raise(10)  # 10% raise
        assert emp.salary == 66000


class TestAnimalInheritance:
    """Test Animal inheritance."""

    def test_dog(self):
        """Test Dog class."""
        dog = Dog("Buddy", "Golden Retriever")
        assert dog.name == "Buddy"
        assert dog.breed == "Golden Retriever"
        assert dog.speak() == "Woof"

    def test_cat(self):
        """Test Cat class."""
        cat = Cat("Whiskers")
        assert cat.name == "Whiskers"
        assert hasattr(cat, "color")
        assert cat.speak() == "Meow"

    def test_animal_abstract(self):
        """Test Animal abstract method."""
        animal = Animal("Generic")
        with pytest.raises(NotImplementedError):
            animal.speak()


class TestShoppingCart:
    """Test ShoppingCart class."""

    def test_add_items(self):
        """Test adding items."""
        cart = ShoppingCart()
        cart.add_item("apple", 3)
        cart.add_item("banana", 2)
        cart.add_item("apple", 2)  # Add more apples

        assert cart.items["apple"] == 5  # Should be 3+2
        assert cart.total_items() == 7  # Total quantity

    def test_remove_item(self):
        """Test removing items."""
        cart = ShoppingCart()
        cart.add_item("apple", 3)

        cart.remove_item("apple")
        assert "apple" not in cart.items

        # Should handle non-existent item gracefully
        cart.remove_item("banana")  # Should not raise exception


class TestEmailValidator:
    """Test EmailValidator class."""

    def test_is_valid(self):
        """Test email validation."""
        assert EmailValidator.is_valid("user@example.com") == True
        assert EmailValidator.is_valid("user.name@example.co.uk") == True
        assert EmailValidator.is_valid("invalid.email") == False
        assert EmailValidator.is_valid("@example.com") == False
        assert EmailValidator.is_valid("user@") == False

    def test_normalize(self):
        """Test email normalization."""
        assert EmailValidator.normalize("USER@EXAMPLE.COM") == "user@example.com"
        assert (
            EmailValidator.normalize("User.Name@Example.Com") == "user.name@example.com"
        )


class TestTemperature:
    """Test Temperature class."""

    def test_celsius_to_fahrenheit(self):
        """Test Celsius to Fahrenheit conversion."""
        temp = Temperature(0)
        assert temp.fahrenheit == 32

        temp = Temperature(100)
        assert temp.fahrenheit == 212

        temp = Temperature(37)
        assert abs(temp.fahrenheit - 98.6) < 0.1

    def test_fahrenheit_setter(self):
        """Test setting temperature via Fahrenheit."""
        temp = Temperature(0)
        temp.fahrenheit = 212
        assert temp.celsius == 100

        temp.fahrenheit = 32
        assert temp.celsius == 0
