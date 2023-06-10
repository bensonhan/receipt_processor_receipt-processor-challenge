from flask import Flask, request, jsonify
import sqlite3
import uuid
from jsonschema import validate

app = Flask(__name__)
app.config['DATABASE'] = ':memory:'

schema = {
    "type": "object",
    "required": ["retailer", "purchaseDate", "purchaseTime", "items", "total"],
    "properties": {
        "retailer": {
            "description": "The name of the retailer or store the receipt is from.",
            "type": "string",
            "pattern": "^\\S+$",
            "example": "Target"
        },
        "purchaseDate": {
            "description": "The date of the purchase printed on the receipt.",
            "type": "string",
            "format": "date",
            "example": "2022-01-01"
        },
        "purchaseTime": {
            "description": "The time of the purchase printed on the receipt. 24-hour time expected.",
            "type": "string",
            "format": "time",
            "example": "13:01"
        },
        "items": {
            "type": "array",
            "minItems": 1,
            "items": {"$ref": "#/components/schemas/Item"}
        },
        "total": {
            "description": "The total amount paid on the receipt.",
            "type": "string",
            "pattern": "^\\d+\\.\\d{2}$",
            "example": "6.49"
        }
    }
}

@app.route('/')
def hello_world():
    return "<p>Hello, World!</p>"

def get_db():
    db = getattr(app, '_database', None)
    if db is None:
        db = app._database = sqlite3.connect(app.config['DATABASE'])
        db.execute('CREATE TABLE IF NOT EXISTS receipts (id STRING PRIMARY KEY, points INTEGER)')
    return db

def calculate_points(data):
    points = 0
    points += count_alphanumeric(data["retailer"])
    return points

def count_alphanumeric(string):
    count = 0
    for char in string:
        if char.isalnum():
            count += 1
    return count

@app.route('/receipts/process', methods=['POST'])
def process_receipt():
    data = request.get_json()
    # try:
    #     validate(data, schema)
    # except:
    #     return "The receipt is invalid", 400
    id = str(uuid.uuid4())
    points = calculate_points(data)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO receipts (id, points) VALUES (?, ?)", (id, points))
    return jsonify({"id": id}), 200

if __name__ == '__main__':
    app.run(debug=True)