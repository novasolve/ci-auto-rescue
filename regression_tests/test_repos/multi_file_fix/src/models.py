class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        
    def can_vote(self):
        # Bug: wrong age threshold
        return self.age >= 21  # Should be 18
        
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price
        
    def apply_discount(self, percentage):
        # Bug: wrong calculation
        discount = self.price * percentage  # Should be percentage / 100
        return self.price - discount
