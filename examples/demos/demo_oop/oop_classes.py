class BankAccount:
    """
    A simple bank account class supporting deposits, withdrawals with overdraft protection,
    and balance inquiries.
    """

    def __init__(self, initial_balance=0):
        # Ensure the initial balance is non-negative
        self._balance = initial_balance if initial_balance >= 0 else 0

    def deposit(self, amount):
        """
        Deposit a positive amount into the account.
        Negative or zero amounts are ignored.
        Returns the current balance.
        """
        if amount > 0:
            self._balance += amount
        return self._balance

    def withdraw(self, amount):
        """
        Withdraw a positive amount from the account.
        If the withdrawal would overdraw the account, it is not performed and 0 is returned.
        On success, returns the amount withdrawn.
        """
        if amount <= 0:
            return 0
        if amount > self._balance:
            return 0
        self._balance -= amount
        return amount

    def get_balance(self):
        """Return the current account balance."""
        return self._balance


class Rectangle:
    """
    A rectangle defined by its width and height.
    Provides methods to compute area and perimeter.
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        """Return the area of the rectangle."""
        return self.width * self.height

    def perimeter(self):
        """Return the perimeter of the rectangle."""
        return 2 * (self.width + self.height)
