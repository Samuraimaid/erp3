#!/usr/bin/env python3
"""Migration: set is_active=True for customers missing the field.

Usage: run inside environment that can access MongoDB (or from host using docker exec).
"""
from pymongo import MongoClient
import os

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://mundo-mongodb:27017")
DB_NAME = os.environ.get("MONGO_DB", "mundo")

def main():
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    res = db.customers.update_many({"is_active": {"$exists": False}}, {"$set": {"is_active": True}})
    print(f"Matched: {res.matched_count}, Modified: {res.modified_count}")

if __name__ == '__main__':
    main()
