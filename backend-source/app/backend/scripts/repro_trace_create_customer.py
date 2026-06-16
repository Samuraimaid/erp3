#!/usr/bin/env python3
"""Reproduce customer create via API and trace which MongoDB DB/collection stored it.

- Logs in via PIN (tries default PIN '01011990').
- Creates a test customer via /api/customers.
- Searches all MongoDB databases for the returned customer_id.
"""
import requests
import os
import time
from pymongo import MongoClient

API_BASE = os.environ.get('API_BASE', 'http://127.0.0.1:3000/api')
PIN_TRY = os.environ.get('TEST_PIN', '01011990')
MONGO = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

session = requests.Session()

def get_pin_users():
    r = session.get(f"{API_BASE}/auth/pin/users")
    r.raise_for_status()
    return r.json()


def login_with_pin(user_id=None):
    payload = {'pin': PIN_TRY}
    if user_id:
        payload['user_id'] = user_id
    r = session.post(f"{API_BASE}/auth/pin/login", json=payload)
    if r.status_code != 200:
        print('Login failed:', r.status_code, r.text)
        r.raise_for_status()
    print('Login OK')
    return r


def create_customer():
    sample = {
        'name': 'TRACE Cliente X',
        'email': 'trace@example.com',
        'phone': '9999-0000',
        'address': 'C/ Test 123'
    }
    r = session.post(f"{API_BASE}/customers", json=sample)
    print('POST /customers ->', r.status_code, r.text)
    r.raise_for_status()
    return r.json()


def find_customer_in_mongo(customer_id):
    client = MongoClient(MONGO)
    matches = []
    for dbname in client.list_database_names():
        db = client[dbname]
        if 'customers' in db.list_collection_names():
            col = db['customers']
            doc = col.find_one({'customer_id': customer_id}, {'_id':0})
            if doc:
                matches.append((dbname, doc))
    return matches


if __name__ == '__main__':
    users = []
    try:
        users = get_pin_users()
    except Exception as e:
        print('Could not fetch pin users:', e)

    user_id = None
    if users:
        print('Found pin users:', [u.get('user_id') for u in users])
        user_id = users[0].get('user_id')

    try:
        login_with_pin(user_id)
    except Exception:
        print('Attempting login without user_id')
        login_with_pin(None)

    created = create_customer()
    cid = created.get('customer_id') or created.get('customerId')
    print('Created customer_id:', cid)

    # small pause to let DB flush
    time.sleep(0.5)

    matches = find_customer_in_mongo(cid)
    if not matches:
        print('No matches found in MongoDB for', cid)
        # print recent customers per DB for debugging
        client = MongoClient(MONGO)
        for dbname in client.list_database_names():
            db = client[dbname]
            if 'customers' in db.list_collection_names():
                cnt = db['customers'].count_documents({})
                print(f"DB {dbname} customers_count={cnt}")
    else:
        for dbname, doc in matches:
            print('Found in DB:', dbname)
            print(doc)
