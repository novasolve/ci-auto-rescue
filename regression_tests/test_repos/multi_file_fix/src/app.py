from services import UserService, ProductService

def create_sample_data():
    user_service = UserService()
    product_service = ProductService()
    
    # Add users
    user_service.add_user("Alice", 25)
    user_service.add_user("Bob", 17)
    user_service.add_user("Charlie", 18)
    
    # Add products
    product_service.add_product("Laptop", 1000)
    product_service.add_product("Mouse", 50)
    
    return user_service, product_service

def get_voting_stats(user_service):
    voters = user_service.get_voters()
    total = len(user_service.users)
    # Bug: division by zero not handled
    percentage = len(voters) / total * 100
    return percentage
