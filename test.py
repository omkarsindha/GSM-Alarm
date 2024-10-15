import json

data = {
    "name": "John Doe",
    "age": 30,
    "city": "Burlington"
}

try:
    with open('data.json', 'w') as file:
        json.dump(data, file, indent=4)
except:
    print("JI file not found")
