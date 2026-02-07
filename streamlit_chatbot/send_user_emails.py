"""
Email Sender Script for ERG AI Tool
Sends emails to users from the database or CSV using Gmail SMTP.
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pymongo import MongoClient

from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# Configuration
# =============================================================================

# Gmail SMTP settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Email credentials from environment
SENDER_EMAIL = os.getenv("GMAIL_SENDER_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


# =============================================================================
# Email Templates
# =============================================================================


def get_welcome_email_body(user_name: str, username: str, password: str) -> str:
    """
    Generate the welcome email body.
    Customize this template as needed.
    """
    return f"""
Dear {user_name},

This email is to inform you that Part 1 (Cohort-1) of the AI-assisted learning study is now live.

ABOUT THIS SESSION
------------------
This session is part of a larger research study examining how different levels of AI support influence learning and reasoning. In this part, you will complete a short learning activity using a custom-built chatbot provided within the study platform.

Estimated Duration: ~20 minutes
Mode: Fully online

IMPORTANT GUIDELINES
--------------------
• Use of external websites or AI tools (e.g., ChatGPT, Gemini, search engines) is not encouraged.
• This study is anonymised, not graded, and conducted purely for research purposes.

CONSENT FORM (Mandatory)
------------------------
Participation requires signing an informed consent form. Please review and sign the consent form using the link below before starting the study:

DocuSign Consent Link: https://docuseal.com/d/AHaoyFqHbtK3KV

• If you don't get your signed consent form then please do check your spam/junk folder as well. If you still don't receive it, please contact us.

NEXT STEPS
----------
Parts 2 and 3 of the study will be shared shortly in separate emails.

We sincerely request your cooperation in completing this session attentively, as your participation is crucial to the success of this research.

ACCESS LINK: https://edunova.moodlecloud.com/login/index.php

Username: {username}
Password: {password}

Thank you for your continued support.

Warm regards,
Yash Nagaraj
"""


def get_custom_email_body(user_name: str, custom_message: str) -> str:
    """
    Generate a custom email body with user personalization.
    """
    return f"""
Dear {user_name},

{custom_message}

Best regards,
ERG AI Tool Team
"""


def get_reminder_email_body(
    user_name: str, cohort_number: int = 1, whatsapp_link: str = None
) -> str:
    """
    Generate a reminder email body for users to complete their cohort.
    """
    whatsapp_section = ""
    if whatsapp_link:
        whatsapp_section = f"""
NEED HELP?
----------
If you face any issues or have questions, please join our WhatsApp group for quick support:

WhatsApp Group: {whatsapp_link}
"""

    return f"""
Dear {user_name},

This is a friendly reminder to complete Cohort-{cohort_number} of the AI-assisted learning study.

IMPORTANT
---------
Please complete your current cohort session as soon as possible so that we can send you the next cohort materials.

If you have already completed the session, please ignore this email.

ACCESS LINK: https://edunova.moodlecloud.com/login/index.php

QUICK REMINDERS
---------------
• Estimated Duration: ~20 minutes
• Use of external AI tools is not encouraged
• This study is anonymised and not graded
{whatsapp_section}
Your participation is crucial to the success of this research. Thank you for your time and cooperation!

Warm regards,
Yash Nagaraj
"""


# =============================================================================
# Database Functions
# =============================================================================


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
        client.admin.command("ping")
        print("✅ Successfully connected to MongoDB")
        return client
    except Exception as e:
        raise ConnectionError(f"Failed to connect to MongoDB: {e}")


def get_users_from_db(db, filter_query: dict = None) -> list:
    """
    Get users from the database.

    Args:
        db: MongoDB database instance
        filter_query: Optional filter query (e.g., {"source": "csv_import"})

    Returns:
        List of user documents
    """
    collection = db["users"]
    query = filter_query or {}
    users = list(collection.find(query, {"password": 0}))  # Exclude hashed password
    print(f"📄 Found {len(users)} users in database")
    return users


def get_new_users_from_db(db, since_hours: int = 24) -> list:
    """
    Get users added in the last N hours.
    """
    from datetime import timedelta

    collection = db["users"]
    cutoff_time = datetime.utcnow() - timedelta(hours=since_hours)

    users = list(
        collection.find({"created_at": {"$gte": cutoff_time}}, {"password": 0})
    )
    print(f"📄 Found {len(users)} users added in the last {since_hours} hours")
    return users


# =============================================================================
# Email Functions
# =============================================================================


def send_email(
    to_email: str, to_name: str, subject: str, body: str, is_html: bool = False
) -> dict:
    """
    Send an email using Gmail SMTP.

    Args:
        to_email: Recipient email address
        to_name: Recipient name
        subject: Email subject
        body: Email body (plain text or HTML)
        is_html: Whether the body is HTML

    Returns:
        dict with success status and message
    """
    if not SENDER_EMAIL or not GMAIL_APP_PASSWORD:
        return {
            "success": False,
            "error": "GMAIL_SENDER_EMAIL or GMAIL_APP_PASSWORD not set in environment",
        }

    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = SENDER_EMAIL
        message["To"] = to_email

        # Attach body
        if is_html:
            part = MIMEText(body, "html")
        else:
            part = MIMEText(body, "plain")
        message.attach(part)

        # Create secure connection and send
        context = ssl.create_default_context()

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, message.as_string())

        return {"success": True, "message": f"Email sent to {to_email}"}

    except smtplib.SMTPAuthenticationError as e:
        return {"success": False, "error": f"Authentication failed: {e}"}
    except smtplib.SMTPException as e:
        return {"success": False, "error": f"SMTP error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_bulk_emails(
    users: list,
    subject: str,
    message_template: str,
    include_credentials: bool = False,
    credentials_map: dict = None,
) -> dict:
    """
    Send emails to multiple users.

    Args:
        users: List of user documents
        subject: Email subject
        message_template: Email message (use {name} for personalization)
        include_credentials: Whether to include login credentials
        credentials_map: Dict mapping username to plain password (for welcome emails)

    Returns:
        Statistics about the email sending process
    """
    stats = {"total": len(users), "sent": 0, "failed": 0, "errors": []}

    print("\n" + "=" * 60)
    print("📧 SENDING EMAILS")
    print("=" * 60 + "\n")

    for user in users:
        email = user.get("email")
        name = user.get("name", "User")
        username = user.get("username", "")

        if not email:
            print(f"⚠️  Skipping {name} - no email address")
            stats["failed"] += 1
            stats["errors"].append({"user": name, "error": "No email address"})
            continue

        # Generate email body
        if include_credentials and credentials_map and username in credentials_map:
            body = get_welcome_email_body(name, username, credentials_map[username])
        else:
            # Personalize the message
            personalized_message = message_template.replace("{name}", name)
            personalized_message = personalized_message.replace("{username}", username)
            personalized_message = personalized_message.replace("{email}", email)
            body = get_custom_email_body(name, personalized_message)

        # Send email
        result = send_email(email, name, subject, body)

        if result["success"]:
            print(f"✅ EMAIL SENT: {name} <{email}>")
            stats["sent"] += 1
        else:
            print(f"❌ FAILED: {name} <{email}> - {result['error']}")
            stats["failed"] += 1
            stats["errors"].append(
                {"user": name, "email": email, "error": result["error"]}
            )

    return stats


def send_to_new_user(db, username: str, plain_password: str, subject: str = None):
    """
    Send welcome email to a specific new user with their credentials.
    """
    collection = db["users"]
    user = collection.find_one({"username": username}, {"password": 0})

    if not user:
        print(f"❌ User '{username}' not found in database")
        return

    email = user.get("email")
    name = user.get("name", username)

    if not email:
        print(f"❌ No email address for user '{username}'")
        return

    subject = subject or "Regarding CHEAL ERG Study Participation"
    body = get_welcome_email_body(name, username, plain_password)

    result = send_email(email, name, subject, body)

    if result["success"]:
        print(f"✅ EMAIL SENT: {name} <{email}>")
    else:
        print(f"❌ FAILED: {name} <{email}> - {result['error']}")

    return result


# =============================================================================
# Main Functions
# =============================================================================


def send_to_all_users(subject: str, message: str):
    """Send an email to all users in the database."""
    try:
        client = get_mongo_client()
        db = client["chatbot_logs"]

        users = get_users_from_db(db)

        if not users:
            print("❌ No users found in database")
            return

        stats = send_bulk_emails(users, subject, message)

        print("\n" + "=" * 60)
        print("📊 EMAIL SENDING SUMMARY")
        print("=" * 60)
        print(f"Total users: {stats['total']}")
        print(f"Emails sent: {stats['sent']}")
        print(f"Failed: {stats['failed']}")

        if stats["errors"]:
            print("\nErrors:")
            for err in stats["errors"]:
                print(f"  - {err['user']}: {err['error']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def send_to_recent_users(subject: str, message: str, hours: int = 24):
    """Send an email to users added in the last N hours."""
    try:
        client = get_mongo_client()
        db = client["chatbot_logs"]

        users = get_new_users_from_db(db, hours)

        if not users:
            print(f"❌ No users found added in the last {hours} hours")
            return

        stats = send_bulk_emails(users, subject, message)

        print("\n" + "=" * 60)
        print("📊 EMAIL SENDING SUMMARY")
        print("=" * 60)
        print(f"Total recent users: {stats['total']}")
        print(f"Emails sent: {stats['sent']}")
        print(f"Failed: {stats['failed']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def send_to_custom_emails(
    email_list: list, subject: str, message: str, names: list = None
) -> dict:
    """
    Send emails to a custom list of email addresses.

    Args:
        email_list: List of email addresses
        subject: Email subject
        message: Email message (use {name} for personalization)
        names: Optional list of names corresponding to emails

    Returns:
        Statistics about the email sending process
    """
    if not email_list:
        print("❌ No email addresses provided")
        return {"total": 0, "sent": 0, "failed": 0, "errors": []}

    # Create user-like dicts for compatibility with send_bulk_emails
    users = []
    for i, email in enumerate(email_list):
        email = email.strip()
        if email:
            name = names[i] if names and i < len(names) else email.split("@")[0]
            users.append(
                {"email": email, "name": name, "username": email.split("@")[0]}
            )

    print(f"\n📧 Sending to {len(users)} custom email address(es)...")

    stats = send_bulk_emails(users, subject, message)

    print("\n" + "=" * 60)
    print("📊 EMAIL SENDING SUMMARY")
    print("=" * 60)
    print(f"Total emails: {stats['total']}")
    print(f"Sent: {stats['sent']}")
    print(f"Failed: {stats['failed']}")

    if stats["errors"]:
        print("\nErrors:")
        for err in stats["errors"]:
            print(f"  - {err.get('email', err.get('user'))}: {err['error']}")

    return stats


def send_single_custom_email(
    to_email: str, subject: str, message: str, to_name: str = None
) -> dict:
    """
    Send a single email to a custom email address.

    Args:
        to_email: Recipient email address
        subject: Email subject
        message: Email message
        to_name: Optional recipient name

    Returns:
        Result dict with success status
    """
    to_name = to_name or to_email.split("@")[0]

    print(f"\n📧 Sending email to {to_name} <{to_email}>...")

    body = get_custom_email_body(to_name, message)
    result = send_email(to_email, to_name, subject, body)

    if result["success"]:
        print(f"✅ EMAIL SENT: {to_name} <{to_email}>")
    else:
        print(f"❌ FAILED: {to_name} <{to_email}> - {result['error']}")

    return result


def send_welcome_email_to_custom(
    to_email: str, to_name: str, username: str, password: str, subject: str = None
) -> dict:
    """
    Send the welcome email template to a custom email address with credentials.
    Uses the same template as the bulk welcome emails.

    Args:
        to_email: Recipient email address
        to_name: Recipient's full name
        username: Login username to include in email
        password: Login password to include in email (plain text)
        subject: Optional custom subject (defaults to welcome subject)

    Returns:
        Result dict with success status
    """
    subject = subject or "ERG AI Learning Study - Part 1 (Cohort-1) Now Live"

    print(f"\n📧 Sending welcome email to {to_name} <{to_email}>...")
    print(f"   Username: {username}")
    print(f"   Password: {'*' * len(password)}")

    body = get_welcome_email_body(to_name, username, password)
    result = send_email(to_email, to_name, subject, body)

    if result["success"]:
        print(f"✅ WELCOME EMAIL SENT: {to_name} <{to_email}>")
    else:
        print(f"❌ FAILED: {to_name} <{to_email}> - {result['error']}")

    return result


def load_credentials_from_csv() -> dict:
    """
    Load username -> password mapping from the CSV file.
    Returns a dict mapping usernames to plain text passwords.
    """
    import csv

    csv_path = os.path.join(
        os.path.dirname(__file__),
        "ERG Study Information form (Responses) - Form Responses 1.csv",
    )

    credentials = {}

    if not os.path.exists(csv_path):
        print(f"⚠️  CSV file not found: {csv_path}")
        return credentials

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = row.get("Username", "").strip()
            password = row.get("Password ", "").strip()  # Note: space in column name
            if username and password:
                credentials[username] = password

    print(f"📄 Loaded {len(credentials)} credentials from CSV")
    return credentials


def send_welcome_emails_to_all(db, users: list) -> dict:
    """
    Send welcome emails with credentials to all users.
    Credentials are loaded from the CSV file.
    """
    credentials = load_credentials_from_csv()

    if not credentials:
        print("❌ No credentials found in CSV. Cannot send welcome emails.")
        return {"total": 0, "sent": 0, "failed": 0, "errors": []}

    stats = {"total": len(users), "sent": 0, "failed": 0, "errors": []}
    subject = "Regarding CHEAL ERG Study Participation"

    print("\n" + "=" * 60)
    print("📧 SENDING WELCOME EMAILS")
    print("=" * 60 + "\n")

    for user in users:
        email = user.get("email")
        name = user.get("name", "User")
        username = user.get("username", "")

        if not email:
            print(f"⚠️  Skipping {name} - no email address")
            stats["failed"] += 1
            stats["errors"].append({"user": name, "error": "No email address"})
            continue

        if username not in credentials:
            print(f"⚠️  Skipping {name} ({username}) - no password in CSV")
            stats["failed"] += 1
            stats["errors"].append({"user": name, "error": "No password in CSV"})
            continue

        password = credentials[username]
        body = get_welcome_email_body(name, username, password)
        result = send_email(email, name, subject, body)

        if result["success"]:
            print(f"✅ EMAIL SENT: {name} <{email}>")
            stats["sent"] += 1
        else:
            print(f"❌ FAILED: {name} <{email}> - {result['error']}")
            stats["failed"] += 1
            stats["errors"].append(
                {"user": name, "email": email, "error": result["error"]}
            )

    return stats


def send_reminder_emails_to_all(
    db, users: list, cohort_number: int = 1, whatsapp_link: str = None
) -> dict:
    """
    Send reminder emails to all users to complete their cohort.
    """
    stats = {"total": len(users), "sent": 0, "failed": 0, "errors": []}
    subject = f"Reminder: Please Complete Cohort-{cohort_number} - ERG Study"

    print("\n" + "=" * 60)
    print("📧 SENDING REMINDER EMAILS")
    print("=" * 60 + "\n")

    for user in users:
        email = user.get("email")
        name = user.get("name", "User")

        if not email:
            print(f"⚠️  Skipping {name} - no email address")
            stats["failed"] += 1
            stats["errors"].append({"user": name, "error": "No email address"})
            continue

        body = get_reminder_email_body(name, cohort_number, whatsapp_link)
        result = send_email(email, name, subject, body)

        if result["success"]:
            print(f"✅ EMAIL SENT: {name} <{email}>")
            stats["sent"] += 1
        else:
            print(f"❌ FAILED: {name} <{email}> - {result['error']}")
            stats["failed"] += 1
            stats["errors"].append(
                {"user": name, "email": email, "error": result["error"]}
            )

    return stats


def schedule_reminder_emails(
    scheduled_time: str,
    cohort_number: int = 1,
    whatsapp_link: str = None,
    filter_query: dict = None,
):
    """
    Schedule reminder emails to be sent at a specific time.

    Args:
        scheduled_time: Time to send in HH:MM format (24-hour)
        cohort_number: Which cohort to remind about
        whatsapp_link: WhatsApp group link for support
        filter_query: Optional MongoDB filter for users
    """
    import time as time_module
    from datetime import datetime, timedelta

    # Parse scheduled time
    try:
        scheduled_hour, scheduled_minute = map(int, scheduled_time.split(":"))
    except ValueError:
        print(f"❌ Invalid time format: {scheduled_time}. Use HH:MM format.")
        return

    # Calculate time until scheduled send
    now = datetime.now()
    scheduled_datetime = now.replace(
        hour=scheduled_hour, minute=scheduled_minute, second=0, microsecond=0
    )

    # If scheduled time has passed today, schedule for tomorrow
    if scheduled_datetime <= now:
        scheduled_datetime += timedelta(days=1)

    wait_seconds = (scheduled_datetime - now).total_seconds()

    print("\n" + "=" * 60)
    print("⏰ SCHEDULED EMAIL SEND")
    print("=" * 60)
    print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scheduled for: {scheduled_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Waiting: {int(wait_seconds // 3600)}h {int((wait_seconds % 3600) // 60)}m")
    print(f"Cohort: {cohort_number}")
    if whatsapp_link:
        print(f"WhatsApp Link: {whatsapp_link}")
    print("=" * 60)
    print("\n⏳ Waiting... (Press Ctrl+C to cancel)")

    try:
        time_module.sleep(wait_seconds)

        print(f"\n🔔 Scheduled time reached! Sending emails...")

        # Connect to database and send
        client = get_mongo_client()
        db = client["chatbot_logs"]
        users = get_users_from_db(db, filter_query)

        if not users:
            print("❌ No users found")
            return

        stats = send_reminder_emails_to_all(db, users, cohort_number, whatsapp_link)

        print("\n" + "=" * 60)
        print("📊 SCHEDULED EMAIL SUMMARY")
        print("=" * 60)
        print(f"Total: {stats['total']}")
        print(f"Sent: {stats['sent']}")
        print(f"Failed: {stats['failed']}")

    except KeyboardInterrupt:
        print("\n\n❌ Scheduled send cancelled by user.")


def interactive_mode():
    """Run in interactive mode to compose and send emails."""
    print("\n" + "=" * 60)
    print("📧 ERG AI Tool - Email Sender (Interactive Mode)")
    print("=" * 60 + "\n")

    # Check environment variables
    if not SENDER_EMAIL:
        print("❌ GMAIL_SENDER_EMAIL not set in .env file")
        return
    if not GMAIL_APP_PASSWORD:
        print("❌ GMAIL_APP_PASSWORD not set in .env file")
        return

    print(f"Sender Email: {SENDER_EMAIL}")
    print()

    # Get recipient selection
    print("What would you like to do?")
    print("─" * 40)
    print("WELCOME EMAILS:")
    print("  1. Send WELCOME emails to ALL users")
    print("  2. Send WELCOME emails to RECENT users (last 24 hours)")
    print("  3. Send WELCOME email to a specific user (by username)")
    print("  6. Send WELCOME email to custom address (manual credentials)")
    print()
    print("REMINDER EMAILS:")
    print("  7. Send REMINDER emails to ALL users (complete cohort)")
    print("  8. SCHEDULE reminder emails for later (e.g., 4pm)")
    print()
    print("OTHER:")
    print("  4. Send custom email to custom address(es)")
    print("  5. Test email (send to yourself)")
    print("─" * 40)

    choice = input("\nEnter choice (1-8): ").strip()

    try:
        client = get_mongo_client()
        db = client["chatbot_logs"]
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    # Handle welcome emails to all users
    if choice == "1":
        users = get_users_from_db(db)
        if not users:
            print("❌ No users found in database")
            return

        print(f"\n📧 Will send welcome emails to {len(users)} users")
        confirm = input("Proceed? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return

        stats = send_welcome_emails_to_all(db, users)

        print("\n" + "=" * 60)
        print("📊 EMAIL SENDING SUMMARY")
        print("=" * 60)
        print(f"Total: {stats['total']}")
        print(f"Sent: {stats['sent']}")
        print(f"Failed: {stats['failed']}")
        if stats["errors"]:
            print("\nErrors:")
            for err in stats["errors"]:
                print(f"  - {err['user']}: {err['error']}")
        return

    # Handle welcome emails to recent users
    if choice == "2":
        users = get_new_users_from_db(db, 24)
        if not users:
            print("❌ No users found added in the last 24 hours")
            return

        print(f"\n📧 Will send welcome emails to {len(users)} recent users")
        confirm = input("Proceed? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return

        stats = send_welcome_emails_to_all(db, users)

        print("\n" + "=" * 60)
        print("📊 EMAIL SENDING SUMMARY")
        print("=" * 60)
        print(f"Total: {stats['total']}")
        print(f"Sent: {stats['sent']}")
        print(f"Failed: {stats['failed']}")
        return

    # Handle welcome email to specific user
    if choice == "3":
        username = input("Enter username: ").strip()
        credentials = load_credentials_from_csv()

        user = db["users"].find_one({"username": username}, {"password": 0})
        if not user:
            print(f"❌ User '{username}' not found")
            return

        if username not in credentials:
            print(f"❌ No password found in CSV for '{username}'")
            return

        email = user.get("email")
        name = user.get("name", username)
        password = credentials[username]

        print(f"\n📧 Will send welcome email to: {name} <{email}>")
        print(f"   Credentials: {username} / {'*' * len(password)}")
        confirm = input("Proceed? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return

        send_welcome_email_to_custom(email, name, username, password)
        return

    # Handle welcome email to custom address with manual credentials
    if choice == "6":
        print("\n--- Send Welcome Email with Credentials ---")
        to_email = input("Recipient email: ").strip()
        to_name = input("Recipient full name: ").strip()
        username = input("Login username: ").strip()
        password = input("Login password: ").strip()

        if not all([to_email, to_name, username, password]):
            print("❌ All fields are required")
            return

        print("\n" + "-" * 40)
        print("Preview:")
        print(f"To: {to_name} <{to_email}>")
        print(f"Subject: Regarding CHEAL ERG Study Participation")
        print(f"Credentials: {username} / {'*' * len(password)}")
        print("-" * 40)

        confirm = input("\nSend welcome email? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return

        send_welcome_email_to_custom(to_email, to_name, username, password)
        return

    # Handle reminder emails to all users
    if choice == "7":
        users = get_users_from_db(db)
        if not users:
            print("❌ No users found in database")
            return

        cohort = input("Which cohort to remind about? (1/2/3) [default: 1]: ").strip()
        cohort_number = int(cohort) if cohort in ["1", "2", "3"] else 1

        whatsapp = input("WhatsApp group link (or press Enter to skip): ").strip()
        whatsapp_link = whatsapp if whatsapp else None

        print(f"\n📧 Will send reminder emails to {len(users)} users")
        print(f"   Cohort: {cohort_number}")
        if whatsapp_link:
            print(f"   WhatsApp: {whatsapp_link}")

        confirm = input("Proceed? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return

        stats = send_reminder_emails_to_all(db, users, cohort_number, whatsapp_link)

        print("\n" + "=" * 60)
        print("📊 REMINDER EMAIL SUMMARY")
        print("=" * 60)
        print(f"Total: {stats['total']}")
        print(f"Sent: {stats['sent']}")
        print(f"Failed: {stats['failed']}")
        return

    # Handle scheduled reminder emails
    if choice == "8":
        print("\n--- Schedule Reminder Emails ---")

        scheduled_time = input(
            "Send at what time? (HH:MM, 24-hour format, e.g., 16:00 for 4pm): "
        ).strip()
        if not scheduled_time:
            scheduled_time = "16:00"

        cohort = input("Which cohort to remind about? (1/2/3) [default: 1]: ").strip()
        cohort_number = int(cohort) if cohort in ["1", "2", "3"] else 1

        whatsapp = input("WhatsApp group link (or press Enter to skip): ").strip()
        whatsapp_link = whatsapp if whatsapp else None

        print(f"\n⏰ Scheduling reminder emails:")
        print(f"   Time: {scheduled_time}")
        print(f"   Cohort: {cohort_number}")
        if whatsapp_link:
            print(f"   WhatsApp: {whatsapp_link}")

        confirm = input("Schedule? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return

        schedule_reminder_emails(scheduled_time, cohort_number, whatsapp_link)
        return

    # Handle custom email (options 4 and 5)
    # Get subject
    subject = input("\nEmail Subject: ").strip()
    if not subject:
        subject = "Message from ERG AI Learning Assistant"

    # Get message
    print("\nEnter your message (press Enter twice to finish):")
    lines = []
    while True:
        line = input()
        if line == "":
            if lines and lines[-1] == "":
                break
            lines.append(line)
        else:
            lines.append(line)
    message = "\n".join(lines[:-1])  # Remove trailing empty line

    if not message:
        print("❌ No message provided. Aborting.")
        return

    print("\n" + "-" * 40)
    print("Preview:")
    print(f"Subject: {subject}")
    print(f"Message:\n{message}")
    print("-" * 40)

    confirm = input("\nSend emails? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        return

    if choice == "4":
        # Custom email addresses
        print(
            "\nEnter email addresses (comma-separated or one per line, empty line to finish):"
        )
        email_input = []
        while True:
            line = input().strip()
            if not line:
                break
            email_input.append(line)

        # Parse emails (handle both comma-separated and line-by-line)
        emails = []
        for item in email_input:
            if "," in item:
                emails.extend([e.strip() for e in item.split(",") if e.strip()])
            else:
                if item:
                    emails.append(item)

        if not emails:
            print("❌ No email addresses provided")
            return

        print(f"\n📧 Will send to {len(emails)} email(s): {', '.join(emails)}")
        users = [
            {"name": e.split("@")[0], "email": e, "username": e.split("@")[0]}
            for e in emails
        ]
    elif choice == "5":
        users = [{"name": "Test User", "email": SENDER_EMAIL, "username": "test"}]
    else:
        print("Invalid choice")
        return

    if not users:
        print("❌ No users found")
        return

    stats = send_bulk_emails(users, subject, message)

    print("\n" + "=" * 60)
    print("📊 EMAIL SENDING SUMMARY")
    print("=" * 60)
    print(f"Total: {stats['total']}")
    print(f"Sent: {stats['sent']}")
    print(f"Failed: {stats['failed']}")


def main():
    """Main entry point."""
    import sys

    print("\n" + "=" * 60)
    print("📧 ERG AI Tool - Email Sender Script")
    print("=" * 60 + "\n")

    # Check environment variables
    if not SENDER_EMAIL:
        print("❌ Error: GMAIL_SENDER_EMAIL not set")
        print("   Add to your .env file: GMAIL_SENDER_EMAIL=your_email@gmail.com")
        return

    if not GMAIL_APP_PASSWORD:
        print("❌ Error: GMAIL_APP_PASSWORD not set")
        print("   Add to your .env file: GMAIL_APP_PASSWORD=your_app_password")
        print("\n   To get an app password:")
        print("   1. Go to https://myaccount.google.com/apppasswords")
        print("   2. Generate a new app password for 'Mail'")
        print("   3. Copy the 16-character password to your .env file")
        return

    print(f"✅ Sender Email: {SENDER_EMAIL}")
    print(f"✅ App Password: {'*' * 12} (configured)")

    if "--interactive" in sys.argv or "-i" in sys.argv:
        interactive_mode()
    elif "--test" in sys.argv:
        # Send test email to yourself
        print("\n📧 Sending test email to yourself...")
        result = send_email(
            SENDER_EMAIL,
            "Test User",
            "Test Email from ERG AI Tool",
            "This is a test email to verify your email configuration is working correctly.",
        )
        if result["success"]:
            print(f"✅ TEST EMAIL SENT to {SENDER_EMAIL}")
        else:
            print(f"❌ TEST FAILED: {result['error']}")
    elif "--to" in sys.argv:
        # Send to custom email from command line
        try:
            to_index = sys.argv.index("--to")
            to_email = sys.argv[to_index + 1]

            # Get subject and message
            subject = "Message from ERG AI Learning Assistant"
            if "--subject" in sys.argv:
                subj_index = sys.argv.index("--subject")
                subject = sys.argv[subj_index + 1]

            if "--message" in sys.argv:
                msg_index = sys.argv.index("--message")
                message = sys.argv[msg_index + 1]
            else:
                print("Enter your message (press Enter twice to finish):")
                lines = []
                while True:
                    line = input()
                    if line == "" and lines and lines[-1] == "":
                        break
                    lines.append(line)
                message = "\n".join(lines[:-1]) if lines else ""

            if not message:
                print("❌ No message provided")
                return

            # Handle multiple emails (comma-separated)
            emails = [e.strip() for e in to_email.split(",") if e.strip()]
            send_to_custom_emails(emails, subject, message)

        except (IndexError, ValueError) as e:
            print(f"❌ Error parsing arguments: {e}")
            print(
                "Usage: python send_user_emails.py --to email@example.com --subject 'Subject' --message 'Message'"
            )
    elif "--schedule" in sys.argv:
        # Schedule reminder emails from command line
        try:
            # Get time (default 16:00)
            scheduled_time = "16:00"
            if "--time" in sys.argv:
                time_index = sys.argv.index("--time")
                scheduled_time = sys.argv[time_index + 1]
            
            # Get cohort (default 1)
            cohort_number = 1
            if "--cohort" in sys.argv:
                cohort_index = sys.argv.index("--cohort")
                cohort_number = int(sys.argv[cohort_index + 1])
            
            # Get WhatsApp link
            whatsapp_link = None
            if "--whatsapp" in sys.argv:
                wa_index = sys.argv.index("--whatsapp")
                whatsapp_link = sys.argv[wa_index + 1]
            
            schedule_reminder_emails(scheduled_time, cohort_number, whatsapp_link)
            
        except (IndexError, ValueError) as e:
            print(f"❌ Error parsing arguments: {e}")
            print("Usage: python send_user_emails.py --schedule --time 16:00 --cohort 1 --whatsapp 'link'")
    elif "--reminder" in sys.argv:
        # Send reminder emails immediately
        try:
            client = get_mongo_client()
            db = client["chatbot_logs"]
            users = get_users_from_db(db)
            
            # Get cohort (default 1)
            cohort_number = 1
            if "--cohort" in sys.argv:
                cohort_index = sys.argv.index("--cohort")
                cohort_number = int(sys.argv[cohort_index + 1])
            
            # Get WhatsApp link
            whatsapp_link = None
            if "--whatsapp" in sys.argv:
                wa_index = sys.argv.index("--whatsapp")
                whatsapp_link = sys.argv[wa_index + 1]
            
            stats = send_reminder_emails_to_all(db, users, cohort_number, whatsapp_link)
            
            print("\n" + "=" * 60)
            print("📊 REMINDER EMAIL SUMMARY")
            print("=" * 60)
            print(f"Total: {stats['total']}")
            print(f"Sent: {stats['sent']}")
            print(f"Failed: {stats['failed']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("\nUsage:")
        print("  python send_user_emails.py --interactive  # Interactive mode")
        print("  python send_user_emails.py --test         # Send test email to yourself")
        print()
        print("  # Custom emails:")
        print("  python send_user_emails.py --to email@example.com --subject 'Subject' --message 'Message'")
        print()
        print("  # Reminder emails (send now):")
        print("  python send_user_emails.py --reminder --cohort 1 --whatsapp 'https://chat.whatsapp.com/xxx'")
        print()
        print("  # Schedule reminder emails:")
        print("  python send_user_emails.py --schedule --time 16:00 --cohort 1 --whatsapp 'https://chat.whatsapp.com/xxx'")
        print()
        print("Or import and use programmatically:")
        print("  from send_user_emails import send_reminder_emails_to_all, schedule_reminder_emails")


if __name__ == "__main__":
    main()
