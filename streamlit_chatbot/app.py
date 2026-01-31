"""
Streamlit Chatbot Application
A cohort-based chatbot powered by Google Gemini API with MongoDB logging.
"""

import json
import os
import uuid
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Load environment variables
load_dotenv()

# Configure page settings
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Configuration and Initialization
# -----------------------------------------------------------------------------

def load_prompts() -> list:
    """Load cohort prompts from JSON file."""
    prompts_path = os.path.join(os.path.dirname(__file__), "prompts.json")
    try:
        with open(prompts_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("prompts.json not found. Please create the configuration file.")
        return []
    except json.JSONDecodeError:
        st.error("Invalid JSON in prompts.json. Please check the file format.")
        return []


def init_gemini() -> bool:
    """Initialize Google Gemini API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        st.error("⚠️ GEMINI_API_KEY not configured. Please add your API key to the .env file.")
        return False
    
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"Failed to configure Gemini API: {e}")
        return False


def get_mongo_client():
    """Get MongoDB client connection."""
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri or mongo_uri == "your_mongodb_uri_here":
        return None
    
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        return client
    except ConnectionFailure:
        st.warning("⚠️ Could not connect to MongoDB. Logging is disabled.")
        return None
    except Exception as e:
        st.warning(f"⚠️ MongoDB error: {e}. Logging is disabled.")
        return None


def log_conversation(
    mongo_client,
    cohort_name: str,
    user_query: str,
    ai_response: str,
    session_id: str
):
    """Log conversation to MongoDB."""
    if mongo_client is None:
        return
    
    try:
        db = mongo_client["chatbot_logs"]
        collection = db["conversations"]
        
        document = {
            "timestamp": datetime.utcnow(),
            "cohort_name": cohort_name,
            "user_query": user_query,
            "ai_response": ai_response,
            "session_id": session_id
        }
        
        collection.insert_one(document)
    except Exception as e:
        st.warning(f"Failed to log conversation: {e}")


def get_gemini_response(system_prompt: str, chat_history: list, user_message: str) -> str:
    """Get response from Gemini API."""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=system_prompt
        )
        
        # Build conversation history for Gemini
        history = []
        for msg in chat_history:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})
        
        # Start chat with history
        chat = model.start_chat(history=history)
        
        # Send new message
        response = chat.send_message(user_message)
        
        return response.text
    
    except Exception as e:
        return f"❌ Error getting response: {e}"


# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------

def init_session_state(cohorts: list):
    """Initialize session state variables."""
    # Generate unique session ID
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    # Track selected cohort
    if "selected_cohort_id" not in st.session_state:
        st.session_state.selected_cohort_id = cohorts[0]["id"] if cohorts else None
    
    # Initialize chat history for each cohort
    if "chat_histories" not in st.session_state:
        st.session_state.chat_histories = {cohort["id"]: [] for cohort in cohorts}


# -----------------------------------------------------------------------------
# UI Components
# -----------------------------------------------------------------------------

def render_sidebar(cohorts: list) -> dict | None:
    """Render sidebar with cohort selection."""
    with st.sidebar:
        st.title("🤖 AI Chatbot")
        st.divider()
        
        st.subheader("Select Cohort")
        
        # Create cohort selection
        cohort_names = [c["name"] for c in cohorts]
        cohort_ids = [c["id"] for c in cohorts]
        
        # Find current index
        current_idx = 0
        if st.session_state.selected_cohort_id in cohort_ids:
            current_idx = cohort_ids.index(st.session_state.selected_cohort_id)
        
        selected_name = st.selectbox(
            "Choose a cohort:",
            cohort_names,
            index=current_idx,
            label_visibility="collapsed"
        )
        
        # Update selected cohort
        selected_idx = cohort_names.index(selected_name)
        st.session_state.selected_cohort_id = cohort_ids[selected_idx]
        
        # Get selected cohort data
        selected_cohort = cohorts[selected_idx]
        
        st.divider()
        
        # Display cohort info
        st.caption("**Current Cohort:**")
        st.info(selected_cohort["name"])
        
        st.divider()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_histories[selected_cohort["id"]] = []
            st.rerun()
        
        st.divider()
        
        # Session info
        st.caption(f"Session: `{st.session_state.session_id[:8]}...`")
        
        return selected_cohort


def render_chat_interface(
    cohort: dict,
    mongo_client,
    gemini_ready: bool
):
    """Render main chat interface."""
    st.title(f"💬 {cohort['name']}")
    
    cohort_id = cohort["id"]
    chat_history = st.session_state.chat_histories[cohort_id]
    
    # Display chat messages
    for message in chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here...", disabled=not gemini_ready):
        # Add user message to history
        chat_history.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Get response (excluding the just-added user message from history)
                response = get_gemini_response(
                    system_prompt=cohort["system_prompt"],
                    chat_history=chat_history[:-1],  # History before current message
                    user_message=prompt
                )
                st.markdown(response)
        
        # Add assistant response to history
        chat_history.append({"role": "assistant", "content": response})
        
        # Update session state
        st.session_state.chat_histories[cohort_id] = chat_history
        
        # Log to MongoDB
        log_conversation(
            mongo_client=mongo_client,
            cohort_name=cohort["name"],
            user_query=prompt,
            ai_response=response,
            session_id=st.session_state.session_id
        )


# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------

def main():
    """Main application entry point."""
    # Load cohort configurations
    cohorts = load_prompts()
    
    if not cohorts:
        st.error("No cohorts configured. Please check prompts.json.")
        st.stop()
    
    # Initialize session state
    init_session_state(cohorts)
    
    # Initialize Gemini API
    gemini_ready = init_gemini()
    
    # Initialize MongoDB (optional - app works without it)
    mongo_client = get_mongo_client()
    
    # Render sidebar and get selected cohort
    selected_cohort = render_sidebar(cohorts)
    
    if selected_cohort:
        # Render main chat interface
        render_chat_interface(
            cohort=selected_cohort,
            mongo_client=mongo_client,
            gemini_ready=gemini_ready
        )
    else:
        st.error("No cohort selected.")


if __name__ == "__main__":
    main()
