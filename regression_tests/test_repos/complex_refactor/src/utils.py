from core import DataManager

def create_manager():
    manager = DataManager()
    # Bug: method doesn't exist yet
    manager.set_default_validators()
    return manager

def process_batch(data_batch):
    manager = create_manager()
    results = []
    for data in data_batch:
        # Bug: wrong method name
        result = manager.proces(data)  # Should be process
        results.extend(result)
    return results
