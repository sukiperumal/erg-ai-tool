"""
AI Learning Assistant
A clean, minimal chatbot with Bloom's taxonomy levels for structured learning.
"""

import uuid
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# Import authentication module
from auth import render_login_page

# Import configuration and initialization module
from config import (
    load_config,
    init_gemini,
    get_mongo_client,
    log_conversation,
    create_or_update_user_session,
    get_gemini_response,
)

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
    }
    
    .stApp, .main, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    
    .stApp p, .stApp span, .stApp div, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #1a1a1a !important;
    }
    
    .stMarkdown, .stMarkdown p, .stMarkdown span {
        color: #1a1a1a !important;
    }
    
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
    
    .level-card {
        background-color: #f8f9fa !important;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .level-card:hover {
        border-color: #007bff;
        background-color: #ffffff !important;
    }
    
    .level-card.selected {
        border-color: #007bff;
        background-color: #e3f2fd !important;
    }
    
    .cohort-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 0.5rem;
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
    
    .blooms-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 15px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-left: 0.5rem;
    }
    
    .blooms-1 { background-color: #ffebee !important; color: #c62828 !important; }
    .blooms-2 { background-color: #fff3e0 !important; color: #ef6c00 !important; }
    .blooms-3 { background-color: #fffde7 !important; color: #f9a825 !important; }
    .blooms-4 { background-color: #e8f5e9 !important; color: #2e7d32 !important; }
    .blooms-5 { background-color: #e3f2fd !important; color: #1565c0 !important; }
    .blooms-6 { background-color: #f3e5f5 !important; color: #7b1fa2 !important; }
    
    section[data-testid="stSidebar"], [data-testid="stSidebar"] > div {
        background-color: #f5f5f5 !important;
        border-right: 1px solid #e0e0e0;
    }
    
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label {
        color: #1a1a1a !important;
    }
    
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
    
    [data-testid="stChatInput"] textarea {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #e0e0e0 !important;
    }
    
    .stButton > button {
        background-color: #b8d4e8 !important;
        color: #2d3748 !important;
        border: none !important;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
        position: relative;
    }
    
    .stButton > button:hover {
        background-color: #a3c7de !important;
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
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background-color: #ffffff !important;
    }
    
    hr {
        border: none;
        border-top: 1px solid #e0e0e0;
        margin: 1.5rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


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

    if "selected_level" not in st.session_state:
        st.session_state.selected_level = None

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

    if "chat_start_time" not in st.session_state:
        st.session_state.chat_start_time = None


def get_chat_key() -> str:
    """Get unique key for current course/cohort/level chat history."""
    if (
        st.session_state.selected_course
        and st.session_state.selected_cohort
        and st.session_state.selected_level
    ):
        return f"{st.session_state.selected_course['id']}_{st.session_state.selected_cohort['id']}_{st.session_state.selected_level}"
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
                st.session_state.selected_level = None
                st.rerun()

        st.markdown("---")

        if st.session_state.current_view == "chat":
            if st.button("← Back", use_container_width=True):
                st.session_state.current_view = "level_selection"
                st.rerun()

            st.markdown("---")

            if (
                st.session_state.selected_course
                and st.session_state.selected_cohort
                and st.session_state.selected_level
            ):
                st.markdown("**Course**")
                st.info(
                    f"{st.session_state.selected_course['icon']} {st.session_state.selected_course['name']}"
                )

                st.markdown("**Cohort**")
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

                st.markdown("**Bloom's Level**")
                level = st.session_state.selected_level
                level_info = st.session_state.selected_cohort["levels"].get(
                    str(level), {}
                )
                level_name = level_info.get("name", f"Level {level}")
                blooms_levels = config.get("blooms_levels", [])
                level_data = next((l for l in blooms_levels if l["id"] == level), None)
                if level_data:
                    st.markdown(
                        f"<span class='blooms-badge blooms-{level}'>{level_data['icon']} {level_name}</span>",
                        unsafe_allow_html=True,
                    )

                st.markdown("---")

                if st.button("🗑️ Clear Chat", use_container_width=True):
                    chat_key = get_chat_key()
                    if chat_key:
                        st.session_state.chat_histories[chat_key] = []
                    st.rerun()

        elif st.session_state.current_view in ["cohort_selection", "level_selection"]:
            if st.button("← Back", use_container_width=True):
                if st.session_state.current_view == "level_selection":
                    st.session_state.current_view = "cohort_selection"
                else:
                    st.session_state.current_view = "course_selection"
                    st.session_state.selected_course = None
                st.rerun()

        # User info and logout at bottom
        if st.session_state.logged_in:
            st.markdown("---")
            st.markdown(f"**Logged in as:** {st.session_state.user_name}")
            if st.button("🚪 Logout", use_container_width=True):
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
                f"Select", key=f"course_{course['id']}", use_container_width=True
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
        # "teacher": {
        #    "icon": "👩‍🏫",
        #    "title": "Teacher Led",
        #    "desc": "AI provides supplementary support. Teacher is the primary instructor.",
        #    "color": "badge-teacher"
        # },
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
                f"Select", key=f"cohort_{cohort['id']}", use_container_width=True
            ):
                st.session_state.selected_cohort = cohort
                st.session_state.current_view = "level_selection"
                st.rerun()


def render_level_selection(config: dict):
    """Render Bloom's taxonomy level selection view."""
    course = st.session_state.selected_course
    cohort = st.session_state.selected_cohort

    if not course or not cohort:
        st.session_state.current_view = "course_selection"
        st.rerun()
        return

    cohort_icons = {"teacher": "👩‍🏫", "hybrid": "🤝", "ai": "🤖"}
    icon = cohort_icons.get(cohort["type"], "🤖")

    st.markdown(
        f'<p class="main-header">{course["icon"]} {course["name"]} — {icon} {cohort["name"]}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sub-header">Select your Bloom\'s Taxonomy level</p>',
        unsafe_allow_html=True,
    )

    blooms_levels = config.get("blooms_levels", [])

    # Create 2 rows of 3 levels each
    for row in range(2):
        cols = st.columns(3)
        for col_idx in range(3):
            level_idx = row * 3 + col_idx
            if level_idx < len(blooms_levels):
                level = blooms_levels[level_idx]
                level_id = level["id"]

                with cols[col_idx]:
                    # Check if this level exists in the cohort
                    level_data = cohort.get("levels", {}).get(str(level_id))

                    if level_data:
                        st.markdown(
                            f"""
                        <div class="level-card">
                            <div style="font-size: 1.5rem; margin-bottom: 0.3rem;">{level["icon"]}</div>
                            <div style="font-weight: 600; color: #1a1a1a;">Level {level_id}: {level["name"]}</div>
                            <div style="font-size: 0.8rem; color: #666;">{level["description"]}</div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        if st.button(
                            f"Start Level {level_id}",
                            key=f"level_{level_id}",
                            use_container_width=True,
                        ):
                            st.session_state.selected_level = level_id
                            st.session_state.current_view = "chat"
                            st.rerun()
                    else:
                        st.markdown(
                            f"""
                        <div class="level-card" style="opacity: 0.5;">
                            <div style="font-size: 1.5rem; margin-bottom: 0.3rem;">{level["icon"]}</div>
                            <div style="font-weight: 600; color: #999;">Level {level_id}: {level["name"]}</div>
                            <div style="font-size: 0.8rem; color: #999;">Not available</div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )


def render_chat_interface(config: dict, mongo_client, gemini_ready: bool):
    """Render the chat interface."""
    course = st.session_state.selected_course
    cohort = st.session_state.selected_cohort
    level = st.session_state.selected_level

    if not course or not cohort or not level:
        st.session_state.current_view = "course_selection"
        st.rerun()
        return

    # Get level data
    level_data = cohort.get("levels", {}).get(str(level), {})
    level_name = level_data.get("name", f"Level {level}")
    system_prompt = level_data.get("system_prompt", "")

    # Header
    cohort_icons = {"teacher": "👩‍🏫", "hybrid": "🤝", "ai": "🤖"}
    cohort_icon = cohort_icons.get(cohort["type"], "🤖")

    blooms_levels = config.get("blooms_levels", [])
    blooms_data = next((l for l in blooms_levels if l["id"] == level), None)
    level_icon = blooms_data["icon"] if blooms_data else "📝"

    st.markdown(
        f'<p class="main-header">{course["icon"]} {course["name"]} — {cohort_icon} {cohort["name"]} — {level_icon} {level_name}</p>',
        unsafe_allow_html=True,
    )

    # Exit Chat button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("🚪 Exit Chat", key="exit_chat_btn", use_container_width=True):
            st.session_state.current_view = "level_selection"
            st.session_state.selected_level = None
            st.rerun()

    # Show resources if available
    resources = level_data.get("resources", [])
    if resources:
        with st.expander("📚 Learning Resources", expanded=False):
            for resource in resources:
                st.markdown(f"• {resource}")

    # Get or initialize chat history
    chat_key = get_chat_key()
    if chat_key not in st.session_state.chat_histories:
        st.session_state.chat_histories[chat_key] = []

    chat_history = st.session_state.chat_histories[chat_key]

    # Display welcome message if no history
    if not chat_history:
        welcome_messages = {
            "teacher": f"Welcome to {course['name']} - {level_name}! I'm here to support your teacher-led learning at this level. Ask me any questions about the material.",
            "hybrid": f"Welcome to {course['name']} - {level_name}! I'm your AI teaching assistant. Let's work through this level together!",
            "ai": f"Welcome to {course['name']} - {level_name}! I'll be your primary instructor for this level. Let's begin!",
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
        chat_history.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner(""):
                response = get_gemini_response(
                    system_prompt=system_prompt,
                    chat_history=chat_history[:-1],
                    user_message=prompt,
                )
                st.markdown(response)

        chat_history.append({"role": "assistant", "content": response})
        st.session_state.chat_histories[chat_key] = chat_history

        log_conversation(
            mongo_client=mongo_client,
            course=course["name"],
            cohort=cohort["name"],
            level=level,
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
            bloom_level=level,
            session_id=st.session_state.session_id,
            chat_entry=chat_entry,
            tokens_used=len(prompt.split()) + len(response.split()),
        )


# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------


def main():
    """Main application entry point."""
    config = load_config()

    if not config.get("courses"):
        st.error("No courses configured. Please check prompts_new.json.")
        st.stop()

    init_session_state(config)
    gemini_ready = init_gemini()
    mongo_client = get_mongo_client()

    # Check if user is logged in
    if not st.session_state.logged_in:
        render_login_page(mongo_client)
        return

    render_sidebar(config, gemini_ready, mongo_client is not None)

    if st.session_state.current_view == "course_selection":
        render_course_selection(config)

    elif st.session_state.current_view == "cohort_selection":
        render_cohort_selection()

    elif st.session_state.current_view == "level_selection":
        render_level_selection(config)

    elif st.session_state.current_view == "chat":
        render_chat_interface(config, mongo_client, gemini_ready)


if __name__ == "__main__":
    main()
