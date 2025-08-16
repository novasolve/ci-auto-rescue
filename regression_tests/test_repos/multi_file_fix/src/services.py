from models import User, Product

class UserService:
    def __init__(self):
        self.users = []
        
    def add_user(self, name, age):
        # Bug: wrong parameter order
        user = User(age, name)  # Should be (name, age)
        self.users.append(user)
        return user
        
    def get_voters(self):
        return [u for u in self.users if u.can_vote()]
        
class ProductService:
    def __init__(self):
        self.products = []
        
    def add_product(self, name, price):
        product = Product(name, price)
        self.products.append(product)
        return product
        
    def apply_sale(self, discount_percentage):
        # Bug: passing percentage incorrectly
        return [p.apply_discount(discount_percentage / 100) for p in self.products]  # Should just pass discount_percentage
