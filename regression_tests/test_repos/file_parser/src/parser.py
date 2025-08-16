import json
import csv

def parse_json(file_path):
    # Bug: doesn't handle file not found
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def parse_csv(file_path):
    # Bug: doesn't return proper list of dicts
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        return list(reader)  # Should use DictReader

def parse_config(file_path):
    # Bug: doesn't handle comments properly
    config = {}
    with open(file_path, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.split('=')  # Bug: doesn't strip whitespace
                config[key] = value
    return config

def count_lines(file_path):
    # Bug: counts empty lines
    with open(file_path, 'r') as f:
        return len(f.readlines())  # Should filter empty lines
