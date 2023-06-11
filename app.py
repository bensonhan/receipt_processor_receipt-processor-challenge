from flask import Flask, request, jsonify
import sqlite3
import uuid
from jsonschema import validate

app = Flask(__name__)
app.config['DATABASE'] = ':memory:'

schema = {
    "type": "object",
    "properties": {
        "retailer": {
        "type": "string"
        },
        "purchaseDate": {
        "type": "string",
        "format": "date"
        },
        "purchaseTime": {
        "type": "string",
        "pattern": "^(?:[01]\\d|2[0-3]):[0-5]\\d$"
        },
        "items": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
            "shortDescription": {
                "type": "string"
            },
            "price": {
                "type": "string",
                "pattern": "^\\d+(\\.\\d{1,2})?$"
            }
            },
            "required": ["shortDescription", "price"]
        }
        },
        "total": {
        "type": "string",
        "pattern": "^\\d+(\\.\\d{1,2})?$"
        }
    },
    "required": ["retailer", "purchaseDate", "purchaseTime", "items", "total"]
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
    try:
        validate(data, schema)
    except:
        return "The receipt is invalid", 400
    id = str(uuid.uuid4())
    points = calculate_points(data)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO receipts (id, points) VALUES (?, ?)", (id, points))
    return jsonify({"id": id}), 200

@app.route('/receipts/<uuid:id>/points', methods=['GET'])
def get_points(id):
    db = get_db()
    cursor = db.cursor()
    res = cursor.execute("SELECT * FROM receipts WHERE id = ?", (str(id),))
    row = res.fetchone()
    return jsonify({"points": row[1]}), 200

if __name__ == '__main__':
    app.run(port=8000, debug=True)