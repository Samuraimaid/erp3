#!/usr/bin/env python3
import requests
import os

API_BASE = os.environ.get('API_BASE', 'http://127.0.0.1:3000/api')

def main():
    s = requests.Session()
    users = s.get(f"{API_BASE}/auth/pin/users").json()
    if not users:
        print('No pin users')
        return
    uid = users[0]['user_id']
    r = s.post(f"{API_BASE}/auth/pin/login", json={'pin':'01011990','user_id':uid})
    print('login status', r.status_code)
    res = s.get(f"{API_BASE}/customers")
    print('GET /customers', res.status_code)
    try:
        js = res.json()
    except Exception as e:
        print('error parsing json', e, res.text)
        return
    print('customers_count=', len(js))
    for c in js[:10]:
        print(c.get('customer_id'), c.get('name'), c.get('is_active'))

if __name__ == '__main__':
    main()
