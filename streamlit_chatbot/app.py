"""
AI Learning Assistant
A clean, minimal chatbot for course-based learning with multiple cohort types.
"""

import json
import os
import uuid
import hashlib
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Load environment variables
load_dotenv()

# -----------------------------------------------------------------------------
# Page Configuration & Custom Styling
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Learning Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for light, minimal design
st.markdown(
    """
<style>
    /* Force light theme */
    :root {
        --background-color: #ffffff;
        --secondary-background-color: #f8f9fa;
        --text-color: #1a1a1a;
        --font: "Source Sans Pro", sans-serif;
    }
    
    /* Main app background */
    .stApp, .main, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    
    /* All text elements */
    .stApp p, .stApp span, .stApp div, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #1a1a1a !important;
    }
    
    /* Markdown text */
    .stMarkdown, .stMarkdown p, .stMarkdown span {
        color: #1a1a1a !important;
    }
    
    /* Clean header styling */
    .main-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1a1a1a !important;
        margin-bottom: 0.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e0e0e0;
    }
    
    .sub-header {
        font-size: 0.95rem;
        color: #555555 !important;
        margin-bottom: 1.5rem;
    }
    
    /* Course card styling */
    .course-card {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }
    
    .course-card:hover {
        border-color: #007bff;
        box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);
    }
    
    .course-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .course-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1a1a !important;
        margin-bottom: 0.3rem;
    }
    
    .course-desc {
        font-size: 0.85rem;
        color: #555555 !important;
    }
    
    /* Cohort badge styling */
    .cohort-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .badge-teacher {
        background-color: #e3f2fd !important;
        color: #1565c0 !important;
    }
    
    .badge-hybrid {
        background-color: #f3e5f5 !important;
        color: #7b1fa2 !important;
    }
    
    .badge-ai {
        background-color: #e8f5e9 !important;
        color: #2e7d32 !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"], [data-testid="stSidebar"] > div {
        background-color: #f5f5f5 !important;
        border-right: 1px solid #e0e0e0;
    }
    
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #1a1a1a !important;
    }
    
    /* Chat message styling */
    [data-testid="stChatMessage"] {
        background-color: #f8f9fa !important;
        border-radius: 12px;
        margin-bottom: 0.5rem;
    }
    
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] div {
        color: #1a1a1a !important;
    }
    
    /* Chat input styling */
    [data-testid="stChatInput"] textarea {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #e0e0e0 !important;
    }
    
    [data-testid="stChatInput"] textarea::placeholder {
        color: #888888 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #5a9bd5 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
        position: relative;
    }
    
    .stButton > button:hover {
        background-color: #4a8bc5 !important;
        transform: translateY(-1px);
        padding-right: 35px !important;
    }
    
    .stButton > button:hover::after {
        content: '→';
        position: absolute;
        right: 12px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 1.1rem;
        opacity: 1;
        transition: all 0.2s ease;
    }
    
    /* Secondary buttons */
    .stButton > button[kind="secondary"] {
        background-color: #f8f9fa !important;
        color: #1a1a1a !important;
        border: 1px solid #e0e0e0 !important;
    }
    
    /* Info/warning/success/error boxes */
    [data-testid="stAlert"] {
        background-color: #f8f9fa !important;
        color: #1a1a1a !important;
    }
    
    .stAlert p, .stAlert span {
        color: #1a1a1a !important;
    }
    
    /* Selectbox styling */
    [data-testid="stSelectbox"] label {
        color: #1a1a1a !important;
    }
    
    [data-testid="stSelectbox"] > div > div {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background-color: #ffffff !important;
    }
    
    /* Divider styling */
    hr {
        border: none;
        border-top: 1px solid #e0e0e0;
        margin: 1.5rem 0;
    }
    
    /* Spinner text */
    .stSpinner > div {
        color: #1a1a1a !important;
    }
    
    /* Column containers */
    [data-testid="column"] {
        background-color: transparent !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Configuration and Initialization
# -----------------------------------------------------------------------------


def load_config() -> dict:
    """Load course and cohort configuration from JSON file."""
    config_path = os.path.join(os.path.dirname(__file__), "prompts.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Configuration file not found. Please create prompts.json.")
        return {"courses": []}
    except json.JSONDecodeError:
        st.error("Invalid JSON in configuration file.")
        return {"courses": []}


def init_gemini() -> bool:
    """Initialize Google Gemini API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return False

    try:
        genai.configure(api_key=api_key)
        return True
    except Exception:
        return False


def get_mongo_client():
    """Get MongoDB client connection."""
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri or mongo_uri == "your_mongodb_uri_here":
        return None

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        return client
    except (ConnectionFailure, Exception):
        return None


def log_conversation(
    mongo_client,
    course: str,
    cohort: str,
    user_query: str,
    ai_response: str,
    session_id: str,
    user_id: str = None,
):
    """Log conversation to MongoDB."""
    if mongo_client is None:
        return

    try:
        db = mongo_client["chatbot_logs"]
        collection = db["conversations"]

        document = {
            "timestamp": datetime.utcnow(),
            "course": course,
            "cohort": cohort,
            "user_query": user_query,
            "ai_response": ai_response,
            "session_id": session_id,
            "user_id": user_id,
        }

        collection.insert_one(document)
    except Exception:
        pass


def create_or_update_user_session(
    mongo_client,
    user_id: str,
    user_name: str,
    course_id: str,
    course_name: str,
    cohort_id: str,
    cohort_name: str,
    bloom_level: str,
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
                # Append to chat_history
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


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(mongo_client, username: str, password: str) -> dict:
    """Authenticate user against MongoDB users collection."""
    if mongo_client is None:
        # Default users when no MongoDB
        default_users = {
            "admin": {
                "password": hash_password("admin123"),
                "user_id": "user_001",
                "name": "Admin User",
            },
            "student": {
                "password": hash_password("student123"),
                "user_id": "user_002",
                "name": "Student User",
            },
            "teacher": {
                "password": hash_password("teacher123"),
                "user_id": "user_003",
                "name": "Teacher User",
            },
        }

        if username in default_users and default_users[username][
            "password"
        ] == hash_password(password):
            return {
                "authenticated": True,
                "user_id": default_users[username]["user_id"],
                "user_name": default_users[username]["name"],
                "username": username,
            }
        return {"authenticated": False}

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
        return {"authenticated": False}


def register_user(mongo_client, username: str, password: str, name: str) -> dict:
    """Register a new user in MongoDB."""
    if mongo_client is None:
        return {"success": False, "message": "Database not available"}

    try:
        db = mongo_client["chatbot_logs"]
        collection = db["users"]

        # Check if user already exists
        if collection.find_one({"username": username}):
            return {"success": False, "message": "Username already exists"}

        # Create new user
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
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_gemini_response(
    system_prompt: str, chat_history: list, user_message: str
) -> str:
    """Get response from Gemini API."""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-3.0-pro", system_instruction=system_prompt
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
# Session State
# -----------------------------------------------------------------------------


def init_session_state(config: dict):
    """Initialize session state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "current_view" not in st.session_state:
        st.session_state.current_view = "login"

    if "selected_course" not in st.session_state:
        st.session_state.selected_course = None

    if "selected_cohort" not in st.session_state:
        st.session_state.selected_cohort = None

    if "chat_histories" not in st.session_state:
        st.session_state.chat_histories = {}

    # Login-related session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    if "user_name" not in st.session_state:
        st.session_state.user_name = None

    if "username" not in st.session_state:
        st.session_state.username = None

    if "bloom_level" not in st.session_state:
        st.session_state.bloom_level = "understanding"

    if "chat_start_time" not in st.session_state:
        st.session_state.chat_start_time = None


def get_chat_key() -> str:
    """Get unique key for current course/cohort chat history."""
    if st.session_state.selected_course and st.session_state.selected_cohort:
        return f"{st.session_state.selected_course['id']}_{st.session_state.selected_cohort['id']}"
    return None


# -----------------------------------------------------------------------------
# UI Components
# -----------------------------------------------------------------------------


def render_sidebar(config: dict, gemini_ready: bool, mongo_ready: bool):
    """Render sidebar with navigation and status."""
    with st.sidebar:
        st.markdown("### 📚 AI Learning Assistant")

        # Home button - always visible when logged in
        if st.session_state.logged_in:
            if st.button("🏠 Home", use_container_width=True, key="home_btn"):
                st.session_state.current_view = "course_selection"
                st.session_state.selected_course = None
                st.session_state.selected_cohort = None
                st.rerun()

        st.markdown("---")

        # Navigation
        if st.session_state.current_view == "chat":
            if st.button("← Back to Courses", use_container_width=True):
                st.session_state.current_view = "course_selection"
                st.rerun()

            st.markdown("---")

            # Current selection info
            if st.session_state.selected_course and st.session_state.selected_cohort:
                st.markdown("**Current Course**")
                st.info(
                    f"{st.session_state.selected_course['icon']} {st.session_state.selected_course['name']}"
                )

                st.markdown("**Cohort Type**")
                cohort_type = st.session_state.selected_cohort["type"]
                if cohort_type == "teacher":
                    st.markdown(
                        '<span class="cohort-badge badge-teacher">👩‍🏫 Teacher Led</span>',
                        unsafe_allow_html=True,
                    )
                elif cohort_type == "hybrid":
                    st.markdown(
                        '<span class="cohort-badge badge-hybrid">🤝 Teacher + AI</span>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<span class="cohort-badge badge-ai">🤖 AI Led</span>',
                        unsafe_allow_html=True,
                    )

                st.markdown("---")

                # Clear chat button
                if st.button("🗑️ Clear Chat", use_container_width=True):
                    chat_key = get_chat_key()
                    if chat_key:
                        st.session_state.chat_histories[chat_key] = []
                    st.rerun()

        # User info and logout at bottom
        if st.session_state.logged_in:
            st.markdown("---")
            st.markdown(f"**Logged in as:** {st.session_state.user_name}")
            if st.button("🚪 Logout", use_container_width=True):
                # Reset session state
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.user_name = None
                st.session_state.username = None
                st.session_state.current_view = "login"
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.chat_histories = {}
                st.rerun()


def render_course_selection(config: dict):
    """Render course selection view."""
    st.markdown('<p class="main-header">Choose Your Course</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Select a course to begin your learning journey</p>',
        unsafe_allow_html=True,
    )

    courses = config.get("courses", [])

    if not courses:
        st.warning("No courses available. Please check the configuration.")
        return

    cols = st.columns(len(courses))

    for idx, course in enumerate(courses):
        with cols[idx]:
            st.markdown(
                f"""
            <div class="course-card">
                <div class="course-icon">{course["icon"]}</div>
                <div class="course-name">{course["name"]}</div>
                <div class="course-desc">{course["description"]}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Select {course['name']}",
                key=f"course_{course['id']}",
                use_container_width=True,
            ):
                st.session_state.selected_course = course
                st.session_state.current_view = "cohort_selection"
                st.rerun()


def render_cohort_selection():
    """Render cohort selection view."""
    course = st.session_state.selected_course

    if not course:
        st.session_state.current_view = "course_selection"
        st.rerun()
        return

    # Back button
    if st.button("← Back to Courses"):
        st.session_state.current_view = "course_selection"
        st.session_state.selected_course = None
        st.rerun()

    st.markdown(
        f'<p class="main-header">{course["icon"]} {course["name"]}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sub-header">Choose your learning cohort type</p>',
        unsafe_allow_html=True,
    )

    cohorts = course.get("cohorts", [])
    cols = st.columns(3)

    cohort_info = {
        "teacher": {
            "icon": "👩‍🏫",
            "title": "Teacher Led",
            "desc": "AI provides supplementary support. Teacher is the primary instructor.",
            "color": "badge-teacher",
        },
        "hybrid": {
            "icon": "🤝",
            "title": "Teacher + AI Led",
            "desc": "AI actively assists teaching. Collaborative learning experience.",
            "color": "badge-hybrid",
        },
        "ai": {
            "icon": "🤖",
            "title": "AI Led",
            "desc": "AI is the primary instructor. Comprehensive autonomous teaching.",
            "color": "badge-ai",
        },
    }

    for idx, cohort in enumerate(cohorts):
        info = cohort_info.get(cohort["type"], cohort_info["ai"])

        with cols[idx]:
            st.markdown(
                f"""
            <div class="course-card">
                <div class="course-icon">{info["icon"]}</div>
                <div class="course-name">{info["title"]}</div>
                <div class="course-desc">{info["desc"]}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Start {info['title']}",
                key=f"cohort_{cohort['id']}",
                use_container_width=True,
            ):
                st.session_state.selected_cohort = cohort
                st.session_state.current_view = "chat"
                st.rerun()


def render_chat_interface(mongo_client, gemini_ready: bool):
    """Render the chat interface."""
    course = st.session_state.selected_course
    cohort = st.session_state.selected_cohort

    if not course or not cohort:
        st.session_state.current_view = "course_selection"
        st.rerun()
        return

    # Header
    cohort_icons = {"teacher": "👩‍🏫", "hybrid": "🤝", "ai": "🤖"}
    icon = cohort_icons.get(cohort["type"], "🤖")

    st.markdown(
        f'<p class="main-header">{course["icon"]} {course["name"]} — {icon} {cohort["name"]}</p>',
        unsafe_allow_html=True,
    )

    # Get or initialize chat history
    chat_key = get_chat_key()
    if chat_key not in st.session_state.chat_histories:
        st.session_state.chat_histories[chat_key] = []

    chat_history = st.session_state.chat_histories[chat_key]

    # Display welcome message if no history
    if not chat_history:
        welcome_messages = {
            "teacher": f"Welcome to {course['name']}! I'm here to support your teacher-led learning. Feel free to ask me any questions about the course material.",
            "hybrid": f"Welcome to {course['name']}! I'm your AI teaching assistant, working alongside your teacher to help you learn. Ask me anything!",
            "ai": f"Welcome to {course['name']}! I'll be your primary instructor. Let's begin your learning journey. What would you like to explore first?",
        }

        with st.chat_message("assistant"):
            st.markdown(welcome_messages.get(cohort["type"], welcome_messages["ai"]))

    # Display chat history
    for message in chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if not gemini_ready:
        st.warning(
            "⚠️ AI is not configured. Please add your Gemini API key to the .env file."
        )
        return

    if prompt := st.chat_input("Type your message..."):
        # Add user message
        chat_history.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner(""):
                response = get_gemini_response(
                    system_prompt=cohort["system_prompt"],
                    chat_history=chat_history[:-1],
                    user_message=prompt,
                )
                st.markdown(response)

        # Add response to history
        chat_history.append({"role": "assistant", "content": response})
        st.session_state.chat_histories[chat_key] = chat_history

        # Log to MongoDB
        log_conversation(
            mongo_client=mongo_client,
            course=course["name"],
            cohort=cohort["name"],
            user_query=prompt,
            ai_response=response,
            session_id=st.session_state.session_id,
            user_id=st.session_state.user_id,
        )

        # Update user session in MongoDB
        chat_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_question": prompt,
            "ai_response": response,
        }

        create_or_update_user_session(
            mongo_client=mongo_client,
            user_id=st.session_state.user_id,
            user_name=st.session_state.user_name,
            course_id=course["id"],
            course_name=course["name"],
            cohort_id=cohort["id"],
            cohort_name=cohort["name"],
            bloom_level=st.session_state.bloom_level,
            session_id=st.session_state.session_id,
            chat_entry=chat_entry,
            tokens_used=len(prompt.split())
            + len(response.split()),  # Approximate token count
        )


# -----------------------------------------------------------------------------
# Login Page
# -----------------------------------------------------------------------------


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

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""<div class="course-card">""", unsafe_allow_html=True)

        # Tabs for Login and Register
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
                            st.session_state.session_id = str(
                                uuid.uuid4()
                            )  # New session on login
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

        st.markdown("</div>", unsafe_allow_html=True)

        # Demo credentials info
        st.markdown("---")
        with st.expander("Demo Credentials (No Database)"):
            st.markdown("""
            If MongoDB is not connected, you can use these demo accounts:
            - **admin** / admin123
            - **student** / student123
            - **teacher** / teacher123
            """)


# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------


def main():
    """Main application entry point."""
    # Load configuration
    config = load_config()

    if not config.get("courses"):
        st.error("No courses configured. Please check prompts.json.")
        st.stop()

    # Initialize
    init_session_state(config)
    gemini_ready = init_gemini()
    mongo_client = get_mongo_client()

    # Check if user is logged in
    if not st.session_state.logged_in:
        render_login_page(mongo_client)
        return

    # Render sidebar (only when logged in)
    render_sidebar(config, gemini_ready, mongo_client is not None)

    # Render main content based on current view
    if st.session_state.current_view == "course_selection":
        render_course_selection(config)

    elif st.session_state.current_view == "cohort_selection":
        render_cohort_selection()

    elif st.session_state.current_view == "chat":
        render_chat_interface(mongo_client, gemini_ready)


if __name__ == "__main__":
    main()
