from core import DataManager
from utils import create_manager

class ExtendedManager(DataManager):
    def __init__(self):
        super().__init__()
        self.cache = {}
        
    def process_with_cache(self, items):
        # Bug: cache key generation is wrong
        cache_key = str(item)  # Bug: should be str(items)
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        result = self.process(items)
        self.cache[cache_key] = result
        return result
        
    def set_default_validators(self):
        # This method is missing in parent class
        self.add_validator('positive', lambda x: x > 0)
        self.add_validator('max_100', lambda x: x <= 100)
