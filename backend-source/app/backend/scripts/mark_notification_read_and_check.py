#!/usr/bin/env python3
import os
import requests

API_BASE = os.environ.get('API_BASE', 'http://127.0.0.1:3000/api')
PIN = os.environ.get('TEST_PIN', '01011990')
NOTIF_ID = os.environ.get('NOTIF_ID', 'notif_86dcb15268dd')

s = requests.Session()

def login():
    r = s.post(f"{API_BASE}/auth/pin/login", json={'pin': PIN})
    print('login', r.status_code)
    r.raise_for_status()

def mark_read(notif_id):
    r = s.put(f"{API_BASE}/notifications/{notif_id}/read")
    print('mark read', r.status_code, r.text)
    r.raise_for_status()

def unread_count():
    r = s.get(f"{API_BASE}/notifications/unread-count")
    print('unread-count', r.status_code, r.text)
    r.raise_for_status()
    return r.json()

if __name__ == '__main__':
    try:
        print('API_BASE ->', API_BASE)
        login()
        mark_read(NOTIF_ID)
        uc = unread_count()
        print('Unread after mark:', uc)
    except Exception as e:
        print('ERROR', e)
