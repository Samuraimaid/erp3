#!/usr/bin/env python3
"""Add 3 test vehicles to every customer via the API.

Usage: set environment variables optionally:
  API_BASE (default http://127.0.0.1:3000/api)
  TEST_PIN   (default 01011990)

The script logs in using PIN auth (first pin user) and posts 3 vehicles per customer.
"""
import os
import time
import random
import requests

API_BASE = os.environ.get('API_BASE', 'http://127.0.0.1:3000/api')
PIN_TRY = os.environ.get('TEST_PIN', '01011990')

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
    r.raise_for_status()
    return r


def get_customers():
    r = session.get(f"{API_BASE}/customers")
    r.raise_for_status()
    return r.json()


SAMPLE_BRANDS = ["TOYOTA", "NISSAN", "HONDA", "CHEVROLET", "KIA"]
SAMPLE_COLORS = ["Blanco", "Negro", "Rojo", "Azul", "Gris"]


def make_plate(idx):
    # Simple pseudo-unique plate: M 9{random 5 digits}
    return f"M {random.randint(10000, 99999)}"


def add_vehicle_for_customer(customer_id, idx):
    plate = make_plate(idx)
    brand = random.choice(SAMPLE_BRANDS)
    model = f"Model-{random.randint(100,999)}"
    year = random.randint(2005, 2024)
    color = random.choice(SAMPLE_COLORS)
    vin = f"VIN{random.randint(100000,999999)}"
    payload = {
        'customer_id': customer_id,
        'plate': plate,
        'brand': brand,
        'model': model,
        'year': year,
        'color': color,
        'vin': vin,
        'vehicle_type': 'sedan'
    }
    r = session.post(f"{API_BASE}/vehicles", json=payload)
    return r


def main():
    print('Using API base:', API_BASE)
    users = []
    try:
        users = get_pin_users()
    except Exception as e:
        print('Could not fetch pin users:', e)
    user_id = None
    if users:
        user_id = users[0].get('user_id')
        print('Found pin user:', user_id)

    try:
        login_with_pin(user_id)
        print('Login successful')
    except Exception as e:
        print('Login failed:', e)
        return

    customers = get_customers()
    print(f'Found {len(customers)} customers')
    for c in customers:
        cid = c.get('customer_id')
        if not cid:
            continue
        print('Adding 3 vehicles for', cid)
        for i in range(3):
            try:
                r = add_vehicle_for_customer(cid, i)
                if r.ok:
                    print('  -> added', r.json().get('vehicle_id'))
                else:
                    print('  -> failed', r.status_code, r.text)
            except Exception as e:
                print('  -> exception', e)
            time.sleep(0.1)


if __name__ == '__main__':
    main()
