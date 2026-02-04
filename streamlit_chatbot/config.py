import json
import os
from datetime import datetime

import streamlit as st
import google.generativeai as genai
from pymongo import MongoClient


# --- Local Storage Paths ---
LOCAL_LOGS_FILE = os.path.join(os.path.dirname(__file__), "local_logs.json")


def load_config() -> dict:
    """Load course and cohort configuration from JSON file."""
    config_path = os.path.join(os.path.dirname(__file__), "prompts_new.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Configuration file not found. Please create prompts_new.json.")
        return {"courses": [], "blooms_levels": []}
    except json.JSONDecodeError:
        st.error("Invalid JSON in configuration file.")
        return {"courses": [], "blooms_levels": []}


# -----------------------------------------------------------------------------
# API Initialization
# -----------------------------------------------------------------------------


def init_gemini() -> bool:
    """Initialize Google Gemini API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return False

    try:
        genai.configure(api_key=api_key)
        return True
    except Exception:
        return False


def get_gemini_response(
    system_prompt: str, chat_history: list, user_message: str
) -> str:
    """Get response from Gemini API."""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash", system_instruction=system_prompt
        )

        history = []
        for msg in chat_history:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=history)
        response = chat.send_message(user_message)

        return response.text

    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}"


# -----------------------------------------------------------------------------
# Database Connection
# -----------------------------------------------------------------------------


def get_mongo_client():
    """Get MongoDB client connection."""
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri or mongo_uri == "your_mongodb_uri_here":
        return None

    try:
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            tls=True,
            tlsAllowInvalidCertificates=True,
        )
        client.admin.command("ping")
        return client
    except Exception:
        # Silently fail - we'll use local storage as fallback
        return None


# -----------------------------------------------------------------------------
# Local Storage Functions
# -----------------------------------------------------------------------------


def load_local_logs():
    """Load conversation logs from local JSON file."""
    if os.path.exists(LOCAL_LOGS_FILE):
        with open(LOCAL_LOGS_FILE, "r") as f:
            return json.load(f)
    return []


def save_local_log(log_entry):
    """Append a log entry to local JSON file."""
    logs = load_local_logs()
    logs.append(log_entry)
    with open(LOCAL_LOGS_FILE, "w") as f:
        json.dump(logs, f, indent=2, default=str)


# -----------------------------------------------------------------------------
# Logging Functions
# -----------------------------------------------------------------------------


def log_conversation(
    mongo_client,
    course: str,
    cohort: str,
    level: int,
    user_query: str,
    ai_response: str,
    session_id: str,
    user_id: str = None,
):
    """Log conversation to MongoDB or local file."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "course": course,
        "cohort": cohort,
        "level": level,
        "user_query": user_query,
        "ai_response": ai_response,
        "session_id": session_id,
        "user_id": user_id,
    }

    if mongo_client is not None:
        try:
            db = mongo_client["chatbot_logs"]
            collection = db["conversations"]
            log_entry["timestamp"] = datetime.utcnow()
            collection.insert_one(log_entry)
            return
        except Exception:
            pass

    # Fallback to local storage
    save_local_log(log_entry)


def create_or_update_user_session(
    mongo_client,
    user_id: str,
    user_name: str,
    course_id: str,
    course_name: str,
    cohort_id: str,
    cohort_name: str,
    bloom_level: int,
    session_id: str,
    chat_entry: dict = None,
    tokens_used: int = 0,
    is_end: bool = False,
):
    """Create or update user session in MongoDB user_sessions collection."""
    if mongo_client is None:
        return

    try:
        db = mongo_client["chatbot_logs"]
        collection = db["user_sessions"]

        # Check if session exists
        existing_session = collection.find_one(
            {"session_id": session_id, "user_id": user_id}
        )

        if existing_session:
            # Update existing session
            update_data = {
                "chat_end_time": datetime.utcnow()
                if is_end
                else existing_session.get("chat_end_time")
            }

            if chat_entry:
                collection.update_one(
                    {"session_id": session_id, "user_id": user_id},
                    {
                        "$push": {"chat_history": chat_entry},
                        "$inc": {"usage_tokens": tokens_used},
                        "$set": update_data,
                    },
                )
            else:
                collection.update_one(
                    {"session_id": session_id, "user_id": user_id},
                    {"$set": update_data, "$inc": {"usage_tokens": tokens_used}},
                )
        else:
            # Create new session
            document = {
                "session_id": session_id,
                "user_id": user_id,
                "user_name": user_name,
                "course_id": course_id,
                "course_name": course_name,
                "cohort_id": cohort_id,
                "cohort_name": cohort_name,
                "bloom_level": bloom_level,
                "chat_start_time": datetime.utcnow(),
                "chat_end_time": None,
                "usage_tokens": tokens_used,
                "chat_history": [chat_entry] if chat_entry else [],
            }

            collection.insert_one(document)
    except Exception:
        pass
