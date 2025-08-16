# Legacy code that needs refactoring to fix tests

# Global state (bad practice)
global_cache = {}
global_counter = 0

def process_item(item):
    # Multiple issues: global state, no error handling, wrong logic
    global global_counter
    global_counter += 1
    
    # Bug: using global cache incorrectly
    if item in global_cache:
        return global_cache[item]
    
    # Complex processing with bugs
    if isinstance(item, str):
        result = item.upper()
    elif isinstance(item, int):
        result = item ** 2  # Bug: should be item * 2
    elif isinstance(item, list):
        # Bug: not handling nested lists properly
        result = [process_item(x) for x in item]
    else:
        result = str(item)
    
    # Bug: cache not being updated
    # global_cache[item] = result
    
    return result

class DataProcessor:
    # This class needs refactoring to fix the tests
    
    def __init__(self):
        # Bug: shared mutable default
        self.data = []  # This should be None and initialized properly
        self.processors = {}
        
    def add_processor(self, type_name, func):
        # Bug: not checking if type_name already exists
        self.processors[type_name] = func
        
    def process(self, items, type_name):
        # Multiple bugs here
        if type_name not in self.processors:
            # Bug: should raise an exception or return None
            return items
            
        processor = self.processors[type_name]
        
        # Bug: not handling exceptions
        results = []
        for item in items:
            result = processor(item)
            results.append(result)
            
        # Bug: modifying internal state incorrectly
        self.data = results  # Should extend, not replace
        
        return results
        
    def get_processed_data(self):
        # Bug: returning mutable internal state
        return self.data  # Should return a copy

def create_processor_chain(*processors):
    # This function needs complete refactoring
    # Bug: chain doesn't work as expected
    def chained(item):
        result = item
        for proc in processors:
            result = proc(item)  # Bug: should pass result, not item
        return result
    return chained
