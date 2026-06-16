#!/usr/bin/env python3
import requests, time
BASE='http://127.0.0.1:8001/api'
print('create-session...')
r = requests.post(BASE+'/test/create-session')
print('status', r.status_code)
print('cookies', r.cookies)
if r.ok:
    token = r.cookies.get('session_token')
    print('session_token', token)
    headers={'Cookie':f'session_token={token}','Content-Type':'application/json'}
    payload={'name':'tmp_e2e','role':'ventas','pin':'12345678'}
    print('posting to /users/pin')
    t0=time.time()
    r2 = requests.post(BASE+'/users/pin', json=payload, headers=headers, timeout=15)
    t1=time.time()
    print('status', r2.status_code)
    print('elapsed', t1-t0)
    print('text', r2.text[:500])
else:
    print('create session failed', r.text)
