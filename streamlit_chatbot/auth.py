"""
Authentication and User Management Module
Handles user registration, login, and local storage fallback.
"""

import json
import os
import uuid
import hashlib
from datetime import datetime

import streamlit as st


# --- Local Storage Paths ---
LOCAL_USERS_FILE = os.path.join(os.path.dirname(__file__), "local_users.json")


def load_local_users():
    """Load users from local JSON file."""
    if os.path.exists(LOCAL_USERS_FILE):
        with open(LOCAL_USERS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_local_users(users):
    """Save users to local JSON file."""
    with open(LOCAL_USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(mongo_client, username: str, password: str) -> dict:
    """Authenticate user against MongoDB or local storage."""

    # ============================================
    # BYPASS AUTHENTICATION FOR TESTING
    # Default credentials: username="test", password="test"
    # ============================================
    # if username == "test" and password == "test":
    #    return {
    #        "authenticated": True,
    #        "user_id": "test-user-123",
    #        "user_name": "Test User",
    #        "username": "test",
    #    }
    ## Also accept any non-empty username/password for testing
    # if username and password:
    #    return {
    #        "authenticated": True,
    #        "user_id": f"user-{username}",
    #        "user_name": username.capitalize(),
    #        "username": username,
    #    }
    # ============================================

    # Try MongoDB first
    if mongo_client is not None:
        try:
            db = mongo_client["chatbot_logs"]
            collection = db["users"]

            user = collection.find_one({"username": username})

            if user and user.get("password") == hash_password(password):
                return {
                    "authenticated": True,
                    "user_id": str(user.get("_id", user.get("user_id", ""))),
                    "user_name": user.get("name", username),
                    "username": username,
                }
            return {"authenticated": False}
        except Exception:
            pass  # Fall through to local storage

    # Fallback to local storage
    local_users = load_local_users()
    if username in local_users:
        stored = local_users[username]
        if stored.get("password") == hash_password(password):
            return {
                "authenticated": True,
                "user_id": stored.get("user_id", ""),
                "user_name": stored.get("name", username),
                "username": username,
            }
    return {"authenticated": False}


def register_user(mongo_client, username: str, password: str, name: str) -> dict:
    """Register a new user in MongoDB or local storage."""

    # Try MongoDB first
    if mongo_client is not None:
        try:
            db = mongo_client["chatbot_logs"]
            collection = db["users"]

            if collection.find_one({"username": username}):
                return {"success": False, "message": "Username already exists"}

            user_id = str(uuid.uuid4())
            document = {
                "user_id": user_id,
                "username": username,
                "password": hash_password(password),
                "name": name,
                "created_at": datetime.utcnow(),
            }

            collection.insert_one(document)
            return {
                "success": True,
                "user_id": user_id,
                "message": "User registered successfully",
            }
        except Exception:
            pass  # Fall through to local storage

    # Fallback to local storage
    local_users = load_local_users()
    if username in local_users:
        return {"success": False, "message": "Username already exists"}

    user_id = str(uuid.uuid4())
    local_users[username] = {
        "user_id": user_id,
        "password": hash_password(password),
        "name": name,
        "created_at": datetime.utcnow().isoformat(),
    }
    save_local_users(local_users)
    return {
        "success": True,
        "user_id": user_id,
        "message": "User registered successfully (local storage)",
    }

    return {"success": False, "message": "Invalid registration data"}


def render_login_page(mongo_client):
    """Render the login page."""
    st.markdown(
        '<p class="main-header">🔐 Login to AI Learning Assistant</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sub-header">Please enter your credentials to continue</p>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input(
                    "Password", type="password", placeholder="Enter your password"
                )

                submit_button = st.form_submit_button("Login", use_container_width=True)

                if submit_button:
                    if username and password:
                        result = authenticate_user(mongo_client, username, password)
                        if result["authenticated"]:
                            st.session_state.logged_in = True
                            st.session_state.user_id = result["user_id"]
                            st.session_state.user_name = result["user_name"]
                            st.session_state.username = result["username"]
                            st.session_state.current_view = "course_selection"
                            st.session_state.session_id = str(uuid.uuid4())
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.warning("Please enter both username and password")

        with tab2:
            with st.form("register_form"):
                new_name = st.text_input(
                    "Full Name", placeholder="Enter your full name"
                )
                new_username = st.text_input(
                    "Username", placeholder="Choose a username", key="reg_username"
                )
                new_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Choose a password",
                    key="reg_password",
                )
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Confirm your password",
                )

                register_button = st.form_submit_button(
                    "Register", use_container_width=True
                )

                if register_button:
                    if new_name and new_username and new_password and confirm_password:
                        if new_password != confirm_password:
                            st.error("Passwords do not match")
                        elif len(new_password) < 6:
                            st.error("Password must be at least 6 characters")
                        else:
                            result = register_user(
                                mongo_client, new_username, new_password, new_name
                            )
                            if result["success"]:
                                st.success(result["message"] + " Please login.")
                            else:
                                st.error(result["message"])
                    else:
                        st.warning("Please fill in all fields")
