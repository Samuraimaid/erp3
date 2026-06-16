#!/usr/bin/env python3
from pymongo import MongoClient
import sys

MONGO = 'mongodb://localhost:27017'

def main():
    client = MongoClient(MONGO)
    dbs = client.list_database_names()
    for name in dbs:
        db = client[name]
        cols = db.list_collection_names()
        if 'customers' in cols:
            col = db.customers
            count = col.count_documents({})
            print(f"DB: {name}  customers: {count}")
            if count:
                sample = list(col.find({}, {'_id':0}).limit(5))
                print(' Sample docs:')
                for d in sample:
                    print('  ', d)
        else:
            print(f"DB: {name}  customers: 0")

if __name__ == '__main__':
    main()
