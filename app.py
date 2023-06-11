from flask import Flask, request, jsonify
import sqlite3
import uuid
from jsonschema import validate
import math

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
            "item": {
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
    if dollar_amount_ends_in(data["total"], 0):
        points += 75
    if dollar_amount_ends_in(data["total"], 25) or dollar_amount_ends_in(data["total"], 50) or dollar_amount_ends_in(data["total"], 75):
        points += 25
    points += int(len(data["items"])/2) * 5
    points += trim_length_multiply(data["items"])
    if is_day_in_purchase_odd(data["purchaseDate"]):
        points += 6
    if is_time_of_purchase_between_two_and_four(data["purchaseTime"]):
        points += 10
    return points

def count_alphanumeric(retailer_name):
    count = 0
    for char in retailer_name:
        if char.isalnum():
            count += 1
    return count

def dollar_amount_ends_in(total_amount, ends_in):
    split_string = total_amount.split('.')
    if len(split_string) < 2:
        # Raise exception
        return False
    if int(split_string[1]) == ends_in:
        return True
    return False

def trim_length_multiply(items):
    points = 0
    for item in items:
        if len(item["shortDescription"].strip()) % 3 == 0:
            points += math.ceil(float(item["price"]) * 0.2)
    return points

def is_day_in_purchase_odd(date):
    split_string = date.split('-')
    if len(split_string) < 3:
        # Raise exception
        return False
    if int(split_string[2]) % 2 == 1:
        return True
    return False

def is_time_of_purchase_between_two_and_four(purchase_time):
    split_string = purchase_time.split(':')
    if len(split_string) < 2:
        # Raise exception
        return False
    hour = int(split_string[0])
    minute = int(split_string[1])
    if hour >= 2 and hour < 4:
        if hour == 2 and minute == 0:
            return False
        return True
    elif hour >= 14 and hour < 16:
        if hour == 14 and minute == 0:
            return False
        return True
    return False

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