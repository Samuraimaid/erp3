#!/usr/bin/env python3
"""Create or update MongoDB collection validator for `customers`.

Requires: pymongo installed and MongoDB reachable via MONGO_URL env var.

Usage examples:
  python backend/scripts/create_customers_validator.py
  MONGO_URL="mongodb://localhost:27017" MONGO_DB="mundo_accesorios_erp" python backend/scripts/create_customers_validator.py
"""
from pymongo import MongoClient, errors
import os
import sys

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("MONGO_DB", os.environ.get("DB_NAME", "mundo_accesorios_erp"))

validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["customer_id", "name", "is_active"],
        "properties": {
            "customer_id": {"bsonType": "string"},
            "name": {"bsonType": "string"},
            "is_active": {"bsonType": "bool"},
        },
    }
}


def main():
    print(f"Connecting to {MONGO_URL} DB={DB_NAME}")
    try:
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
    except errors.PyMongoError as e:
        print("Could not connect to MongoDB:", e)
        sys.exit(2)

    coll_name = "customers"
    try:
        if coll_name in db.list_collection_names():
            print(f"Updating validator on existing collection '{coll_name}'")
            cmd = {
                "collMod": coll_name,
                "validator": validator,
                "validationLevel": "moderate",
            }
            res = db.command(cmd)
            print("collMod result:", res)
        else:
            print(f"Creating collection '{coll_name}' with validator")
            db.create_collection(coll_name, validator=validator)
            print("Collection created")
    except errors.OperationFailure as e:
        print("Operation failed:", e)
        sys.exit(3)
    except Exception as e:
        print("Unexpected error:", e)
        sys.exit(4)

    print("Validator applied successfully")


if __name__ == '__main__':
    main()
