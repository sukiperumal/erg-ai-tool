"""
User Ingestion Script for ERG AI Tool
Reads users from CSV and ingests them into MongoDB with schema validation.
"""

import csv
import os
import hashlib
import uuid
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, OperationFailure

# Load environment variables
from dotenv import load_dotenv

load_dotenv()


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 (matching auth.py implementation)."""
    return hashlib.sha256(password.encode()).hexdigest()


def get_mongo_client():
    """Get MongoDB client connection."""
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable is not set")

    try:
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            tls=True,
            tlsAllowInvalidCertificates=True,
        )
        # Test connection
        client.admin.command("ping")
        print("✅ Successfully connected to MongoDB")
        return client
    except Exception as e:
        raise ConnectionError(f"Failed to connect to MongoDB: {e}")


def setup_users_collection_with_validation(db):
    """
    Setup the users collection with JSON schema validation.
    This ensures all documents follow the required structure.
    """
    # Define the JSON schema for user documents
    user_schema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["user_id", "username", "password", "name", "created_at"],
            "properties": {
                "user_id": {
                    "bsonType": "string",
                    "description": "Unique user identifier (UUID)",
                },
                "username": {
                    "bsonType": "string",
                    "description": "Unique username for login",
                },
                "password": {
                    "bsonType": "string",
                    "description": "SHA-256 hashed password",
                },
                "name": {"bsonType": "string", "description": "Full name of the user"},
                "email": {
                    "bsonType": "string",
                    "description": "Email address of the user",
                },
                "semester": {
                    "bsonType": "string",
                    "description": "Current semester of the user",
                },
                "module_cohort_1": {
                    "bsonType": ["string", "null"],
                    "description": "Module for Cohort 1",
                },
                "module_cohort_2": {
                    "bsonType": ["string", "null"],
                    "description": "Module for Cohort 2",
                },
                "module_cohort_3": {
                    "bsonType": ["string", "null"],
                    "description": "Module for Cohort 3",
                },
                "registration_timestamp": {
                    "bsonType": "string",
                    "description": "Original registration timestamp from form",
                },
                "created_at": {
                    "bsonType": "date",
                    "description": "Document creation timestamp",
                },
                "source": {
                    "bsonType": "string",
                    "description": "Source of user data (csv_import or registration)",
                },
            },
        }
    }

    try:
        # Try to create collection with validation
        db.create_collection("users", validator=user_schema)
        print("✅ Created 'users' collection with schema validation")
    except CollectionInvalid:
        # Collection already exists, update validation
        try:
            db.command("collMod", "users", validator=user_schema)
            print("✅ Updated 'users' collection with schema validation")
        except OperationFailure as e:
            print(f"⚠️ Could not update validation (may already exist): {e}")

    # Create unique index on username to prevent duplicates
    db.users.create_index("username", unique=True)
    print("✅ Created unique index on 'username' field")

    # Create index on email for faster lookups
    db.users.create_index("email")
    print("✅ Created index on 'email' field")


def read_csv_users(csv_path: str) -> list:
    """Read users from CSV file."""
    users = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            user = {
                "timestamp": row.get("Timestamp", "").strip(),
                "name": row.get("Name", "").strip(),
                "email": row.get("Email ID", "").strip(),
                "semester": row.get("Current Semester", "").strip(),
                "module_cohort_1": row.get("Module -Cohort 1", "").strip() or None,
                "module_cohort_2": row.get("Module Cohort-2", "").strip() or None,
                "module_cohort_3": row.get("Module Cohort-3", "").strip() or None,
                "password": row.get(
                    "Password ", ""
                ).strip(),  # Note: space in column name
                "username": row.get("Username", "").strip(),
            }
            users.append(user)

    print(f"📄 Read {len(users)} users from CSV")
    return users


def ingest_users(db, users: list) -> dict:
    """
    Ingest users into MongoDB.
    Returns statistics about the ingestion process.
    """
    stats = {"total": len(users), "inserted": 0, "skipped": 0, "errors": []}

    collection = db["users"]

    for user in users:
        # Check if user already exists
        existing = collection.find_one({"username": user["username"]})
        if existing:
            print(f"⏭️  Skipping '{user['username']}' - already exists")
            stats["skipped"] += 1
            continue

        # Create document matching the schema
        document = {
            "user_id": str(uuid.uuid4()),
            "username": user["username"],
            "password": hash_password(user["password"]),
            "name": user["name"],
            "email": user["email"],
            "semester": user["semester"],
            "module_cohort_1": user["module_cohort_1"],
            "module_cohort_2": user["module_cohort_2"],
            "module_cohort_3": user["module_cohort_3"],
            "registration_timestamp": user["timestamp"],
            "created_at": datetime.utcnow(),
            "source": "csv_import",
        }

        try:
            collection.insert_one(document)
            print(f"✅ Inserted user: {user['username']} ({user['name']})")
            stats["inserted"] += 1
        except Exception as e:
            print(f"❌ Error inserting '{user['username']}': {e}")
            stats["errors"].append({"username": user["username"], "error": str(e)})

    return stats


def verify_users(db, users: list):
    """
    Query and verify each user was added to the database.
    """
    print("\n" + "=" * 60)
    print("🔍 VERIFICATION: Querying each user in the database")
    print("=" * 60 + "\n")

    collection = db["users"]
    verified = 0
    not_found = 0

    for user in users:
        username = user["username"]
        result = collection.find_one(
            {"username": username},
            {"_id": 0, "password": 0},  # Exclude sensitive fields
        )

        if result:
            print(f"✅ VERIFIED: {username}")
            print(f"   Name: {result.get('name')}")
            print(f"   Email: {result.get('email')}")
            print(f"   Semester: {result.get('semester')}")
            modules = []
            if result.get("module_cohort_1"):
                modules.append(f"Cohort1:{result['module_cohort_1']}")
            if result.get("module_cohort_2"):
                modules.append(f"Cohort2:{result['module_cohort_2']}")
            if result.get("module_cohort_3"):
                modules.append(f"Cohort3:{result['module_cohort_3']}")
            if modules:
                print(f"   Modules: {', '.join(modules)}")
            print(f"   User ID: {result.get('user_id')}")
            print(f"   Source: {result.get('source')}")
            print()
            verified += 1
        else:
            print(f"❌ NOT FOUND: {username}")
            not_found += 1

    print("=" * 60)
    print(f"📊 Verification Summary: {verified} verified, {not_found} not found")
    print("=" * 60)

    return verified, not_found


def get_all_users_summary(db):
    """Print a summary of all users in the database."""
    collection = db["users"]

    print("\n" + "=" * 60)
    print("📋 ALL USERS IN DATABASE")
    print("=" * 60 + "\n")

    # Get count by source
    csv_count = collection.count_documents({"source": "csv_import"})
    registered_count = collection.count_documents({"source": {"$ne": "csv_import"}})
    total_count = collection.count_documents({})

    print(f"Total Users: {total_count}")
    print(f"  - Imported from CSV: {csv_count}")
    print(f"  - Self-registered: {registered_count}")

    # Get count by module
    print("\nUsers by Module:")
    for module in ["SA", "CL", "ECBA"]:
        count = collection.count_documents(
            {
                "$or": [
                    {"module_cohort_1": module},
                    {"module_cohort_2": module},
                    {"module_cohort_3": module},
                ]
            }
        )
        print(f"  - {module}: {count}")


def main():
    """Main function to run the user ingestion process."""
    print("\n" + "=" * 60)
    print("🚀 ERG AI Tool - User Ingestion Script")
    print("=" * 60 + "\n")

    # CSV file path
    csv_path = os.path.join(
        os.path.dirname(__file__),
        "ERG Study Information form (Responses) - Form Responses 1.csv",
    )

    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return

    try:
        # Connect to MongoDB
        client = get_mongo_client()
        db = client["chatbot_logs"]

        # Setup collection with validation
        print("\n📦 Setting up collection with schema validation...")
        setup_users_collection_with_validation(db)

        # Read users from CSV
        print("\n📖 Reading users from CSV...")
        users = read_csv_users(csv_path)

        # Ingest users
        print("\n💾 Ingesting users into MongoDB...")
        stats = ingest_users(db, users)

        # Print ingestion summary
        print("\n" + "=" * 60)
        print("📊 INGESTION SUMMARY")
        print("=" * 60)
        print(f"Total users in CSV: {stats['total']}")
        print(f"Successfully inserted: {stats['inserted']}")
        print(f"Skipped (already exist): {stats['skipped']}")
        print(f"Errors: {len(stats['errors'])}")
        if stats["errors"]:
            for err in stats["errors"]:
                print(f"  - {err['username']}: {err['error']}")

        # Verify all users
        verify_users(db, users)

        # Print overall summary
        get_all_users_summary(db)

        print("\n✅ User ingestion complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
