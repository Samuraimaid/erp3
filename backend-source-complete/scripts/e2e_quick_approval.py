#!/usr/bin/env python3
import os
import time
import requests

API_BASE = os.environ.get('API_BASE', 'http://127.0.0.1:3000/api')
PIN = os.environ.get('TEST_PIN', '01011990')

s = requests.Session()

def login():
    r = s.post(f"{API_BASE}/auth/pin/login", json={'pin': PIN})
    print('login status', r.status_code)
    r.raise_for_status()
    print('login resp', r.json())

def get_customers():
    r = s.get(f"{API_BASE}/customers")
    r.raise_for_status()
    return r.json()

def create_vehicle(customer_id):
    payload = {
        'customer_id': customer_id,
        'plate': f'M {int(time.time()) % 99999}',
        'brand': 'TESTBRAND',
        'model': 'TESTMODEL',
        'year': 2020,
        'color': 'Azul prueba',
        'vin': f'VIN{int(time.time())}',
        'vehicle_type': 'sedan'
    }
    r = s.post(f"{API_BASE}/vehicles", json=payload)
    print('create vehicle', r.status_code, r.text)
    r.raise_for_status()
    return r.json().get('vehicle_id')

def create_approval(vehicle_id):
    payload = {
        'type': 'delete_vehicle',
        'payload': {'vehicle_id': vehicle_id},
        'reason': 'Prueba E2E: eliminar vehículo de prueba'
    }
    r = s.post(f"{API_BASE}/approvals", json=payload)
    print('create approval', r.status_code, r.text)
    r.raise_for_status()
    return r.json().get('approval_id')

def list_approvals():
    r = s.get(f"{API_BASE}/approvals")
    print('list approvals', r.status_code)
    if r.ok:
        return r.json()
    return None

def approve(approval_id):
    r = s.put(f"{API_BASE}/approvals/{approval_id}/approve")
    print('approve', r.status_code, r.text)
    r.raise_for_status()
    return r.json()

def get_notifications():
    r = s.get(f"{API_BASE}/notifications")
    print('notifications', r.status_code, r.text)
    r.raise_for_status()
    return r.json()

def unread_count():
    r = s.get(f"{API_BASE}/notifications/unread-count")
    print('unread-count', r.status_code, r.text)
    r.raise_for_status()
    return r.json()


def main():
    try:
        print('API_BASE ->', API_BASE)
        login()
        customers = get_customers()
        if not customers:
            print('No customers found')
            return
        cust = customers[0]
        print('Using customer', cust.get('customer_id'), cust.get('name'))
        vehicle_id = create_vehicle(cust.get('customer_id'))
        print('Vehicle created', vehicle_id)
        approval_id = create_approval(vehicle_id)
        print('Approval created', approval_id)
        # list approvals
        apps = list_approvals()
        print('Approvals count', len(apps) if apps else 0)
        # approve
        resp = approve(approval_id)
        print('Approve response', resp)
        # notifications
        notes = get_notifications()
        print('Notifications count', len(notes))
        print(notes[:5])
        # unread
        uc = unread_count()
        print('Unread', uc)
    except Exception as e:
        print('ERROR', e)

if __name__ == '__main__':
    main()
