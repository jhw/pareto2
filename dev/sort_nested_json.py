import json

def sort_nested_json(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            obj[key] = sort_nested_json(value)
    elif isinstance(obj, list):
        if all(isinstance(item, dict) and 'name' in item for item in obj):
            obj.sort(key=lambda x: x['name'])
        elif all(isinstance(item, str) for item in obj):
            obj.sort()
        else:
            raise RuntimeError("list contains unsupported types or is missing 'name' field in dicts")
    return obj

# Example usage
nested_json = {
    "foo": {
        "employees": [
            {"name": "John", "age": 30},
            {"name": "Alice", "age": 28},
            {"name": "Bob", "age": 25}
        ],
        "departments": ["Sales", "IT", "HR"]
    },
    "bar": "whatevs"
}

try:
    sorted_json = sort_nested_json(nested_json)
    print (json.dumps(sorted_json,
                      sort_keys=True,
                      indent=2))
except RuntimeError as e:
    print(f"Error: {e}")
