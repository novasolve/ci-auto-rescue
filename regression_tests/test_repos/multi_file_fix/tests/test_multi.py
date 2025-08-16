import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import User, Product
from services import UserService, ProductService
from app import create_sample_data, get_voting_stats
import pytest

def test_user_voting_age():
    user1 = User("Alice", 17)
    user2 = User("Bob", 18)
    user3 = User("Charlie", 25)
    
    assert user1.can_vote() == False
    assert user2.can_vote() == True
    assert user3.can_vote() == True
    
def test_product_discount():
    product = Product("Laptop", 1000)
    discounted_price = product.apply_discount(10)  # 10% discount
    assert discounted_price == 900
    
def test_user_service():
    service = UserService()
    user = service.add_user("John", 30)
    assert user.name == "John"
    assert user.age == 30
    
def test_product_service():
    service = ProductService()
    service.add_product("Item1", 100)
    service.add_product("Item2", 200)
    
    sale_prices = service.apply_sale(20)  # 20% off
    assert sale_prices[0] == 80
    assert sale_prices[1] == 160
    
def test_voting_stats():
    user_service, _ = create_sample_data()
    percentage = get_voting_stats(user_service)
    assert percentage == 66.66666666666666  # 2 out of 3 users can vote (18+)
