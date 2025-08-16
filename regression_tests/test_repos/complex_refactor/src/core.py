class DataManager:
    def __init__(self):
        self.data = []
        self.validators = []  # Bug: should be a dict
        
    def add_validator(self, name, func):
        # Bug: treating list as dict
        self.validators[name] = func
        
    def validate(self, item):
        # Bug: iterating over list incorrectly
        for name, validator in self.validators.items():
            if not validator(item):
                return False
        return True
        
    def process(self, items):
        # Bug: wrong variable name
        valid_items = []
        for item in items:
            if self.validate(item):
                valid_item.append(item)  # Bug: should be valid_items
        return valid_items
