"""
User Ingestion Script for ERG AI Tool
Reads users from CSV and ingests them into MongoDB with schema validation.
"""

import csv
import os
import hashlib
import uuid
import random
import string
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, OperationFailure

# Load environment variables
from dotenv import load_dotenv

load_dotenv()


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 (matching auth.py implementation)."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_password(length: int = 12) -> str:
    """
    Generate a secure random password.
    Includes uppercase, lowercase, digits, and special characters.
    """
    # Ensure at least one of each type
    password = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice("!@#$%&*"),
    ]

    # Fill the rest with random characters
    all_chars = string.ascii_letters + string.digits + "!@#$%&*"
    password.extend(random.choice(all_chars) for _ in range(length - 4))

    # Shuffle to randomize positions
    random.shuffle(password)
    return "".join(password)


def generate_username(email: str, name: str = None) -> str:
    """
    Generate a username from email or name.
    Uses email prefix and adds random suffix if needed.
    """
    # Use email prefix
    username = email.split("@")[0].lower()

    # Clean up the username (remove special chars except underscore)
    username = "".join(c for c in username if c.isalnum() or c == "_")

    # Add random suffix if username is too short
    if len(username) < 4:
        username = username + str(random.randint(100, 999))

    return username


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


def read_csv_users(csv_path: str, auto_generate_credentials: bool = True) -> tuple:
    """
    Read users from CSV file.
    If auto_generate_credentials is True, generates missing username/password.

    Returns:
        tuple: (users list, updated_rows list for CSV update)
    """
    users = []
    updated_rows = []
    needs_update = False

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        for row in reader:
            # Check if credentials are missing
            password = row.get("Password ", "").strip()
            username = row.get("Username", "").strip()
            email = row.get("Email ID", "").strip()
            name = row.get("Name", "").strip()

            # Generate missing credentials
            if not password:
                password = generate_password()
                row["Password "] = password
                needs_update = True
                print(f"🔑 Generated password for: {name}")

            if not username:
                username = generate_username(email, name)
                row["Username"] = username
                needs_update = True
                print(f"👤 Generated username for: {name} -> {username}")

            updated_rows.append(row)

            user = {
                "timestamp": row.get("Timestamp", "").strip(),
                "name": name,
                "email": email,
                "semester": row.get("Current Semester", "").strip(),
                "module_cohort_1": row.get("Module -Cohort 1", "").strip() or None,
                "module_cohort_2": row.get("Module Cohort-2", "").strip() or None,
                "module_cohort_3": row.get("Module Cohort-3", "").strip() or None,
                "password": password,
                "username": username,
            }
            users.append(user)

    print(f"📄 Read {len(users)} users from CSV")

    # Return users, updated rows, fieldnames, and whether update is needed
    return users, updated_rows, fieldnames, needs_update


def update_csv_with_credentials(csv_path: str, rows: list, fieldnames: list):
    """
    Update the CSV file with generated credentials.
    Creates a backup before updating.
    """
    import shutil

    # Create backup
    backup_path = csv_path + ".backup"
    shutil.copy2(csv_path, backup_path)
    print(f"📁 Created backup: {backup_path}")

    # Write updated CSV
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Updated CSV with generated credentials")


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


def find_new_users(db, csv_users: list) -> list:
    """
    Compare CSV users with database and return only new users.
    Checks by both username and email to avoid duplicates.
    """
    collection = db["users"]
    new_users = []
    existing_usernames = []
    existing_emails = []

    print("\n🔍 Checking for new users in CSV...")

    for user in csv_users:
        # Check if username already exists
        existing_by_username = collection.find_one({"username": user["username"]})
        # Check if email already exists
        existing_by_email = collection.find_one({"email": user["email"]})

        if existing_by_username:
            existing_usernames.append(user["username"])
        elif existing_by_email:
            existing_emails.append(user["email"])
            print(f"⚠️  User with email '{user['email']}' exists but different username")
        else:
            new_users.append(user)
            print(f"🆕 NEW: {user['username']} ({user['name']}) - {user['email']}")

    print(f"\n📊 Comparison Results:")
    print(f"   Total in CSV: {len(csv_users)}")
    print(f"   Already in DB (by username): {len(existing_usernames)}")
    print(f"   Already in DB (by email): {len(existing_emails)}")
    print(f"   New users to add: {len(new_users)}")

    return new_users


def sync_new_users(db, csv_path: str) -> dict:
    """
    Sync new users from CSV to database.
    Only adds users that don't already exist.
    Returns statistics about the sync process.
    """
    print("\n" + "=" * 60)
    print("🔄 SYNC MODE: Finding and adding new users only")
    print("=" * 60)

    # Read all users from CSV (with auto-generated credentials if needed)
    csv_users, updated_rows, fieldnames, needs_update = read_csv_users(csv_path)

    # Update CSV if credentials were generated
    if needs_update:
        update_csv_with_credentials(csv_path, updated_rows, fieldnames)

    # Find new users
    new_users = find_new_users(db, csv_users)

    if not new_users:
        print("\n✅ No new users to add. Database is up to date!")
        return {
            "total_in_csv": len(csv_users),
            "new_users": 0,
            "inserted": 0,
            "errors": [],
        }

    # Ingest only new users
    print(f"\n💾 Adding {len(new_users)} new user(s) to database...")
    stats = ingest_users(db, new_users)

    # Verify the newly added users
    if stats["inserted"] > 0:
        print("\n🔍 Verifying newly added users...")
        verify_users(db, new_users)

    return {
        "total_in_csv": len(csv_users),
        "new_users": len(new_users),
        "inserted": stats["inserted"],
        "errors": stats["errors"],
    }


def main():
    """Main function to run the user ingestion process."""
    import sys

    # Check for command line arguments
    full_import = "--full" in sys.argv
    mode = "FULL IMPORT" if full_import else "SYNC (new users only)"

    print("\n" + "=" * 60)
    print("🚀 ERG AI Tool - User Ingestion Script")
    print(f"   Mode: {mode}")
    print("=" * 60 + "\n")

    if not full_import:
        print("ℹ️  Running in SYNC mode (default). Use --full for complete re-import.")

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

        if full_import:
            # Full import mode - read and ingest all users
            print("\n📖 Reading users from CSV...")
            users, updated_rows, fieldnames, needs_update = read_csv_users(csv_path)

            # Update CSV if credentials were generated
            if needs_update:
                update_csv_with_credentials(csv_path, updated_rows, fieldnames)

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
        else:
            # Sync mode - only add new users
            stats = sync_new_users(db, csv_path)

            # Print sync summary
            print("\n" + "=" * 60)
            print("📊 SYNC SUMMARY")
            print("=" * 60)
            print(f"Total users in CSV: {stats['total_in_csv']}")
            print(f"New users found: {stats['new_users']}")
            print(f"Successfully inserted: {stats['inserted']}")
            print(f"Errors: {len(stats['errors'])}")
            if stats["errors"]:
                for err in stats["errors"]:
                    print(f"  - {err['username']}: {err['error']}")

        # Print overall summary
        get_all_users_summary(db)

        print("\n✅ User ingestion complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
