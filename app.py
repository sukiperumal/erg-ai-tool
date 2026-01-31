import streamlit as st

st.set_page_config(
    page_title="Erg AI Tool",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

def login():
    st.title("Sign in to your account")
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com", value="jane@edunova.com")
        password = st.text_input("Password", type="password", placeholder="••••••••", value="password123")
        
        submitted = st.form_submit_button("Sign in")

        if submitted:
            if email == 'jane@edunova.com' and password == 'password123':
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Incorrect email or password")

def main_app():
    st.title("Welcome to ERG Study - AI ✨")
    st.sidebar.success("Select a page above.")

    st.markdown("Please choose your Course from below to get started.")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Criminal Law", use_container_width=True):
            st.switch_page("pages/1_Criminal_Law.py")

    with col2:
        if st.button("Stroke Analysis", use_container_width=True):
            st.switch_page("pages/2_Stroke_Analysis.py")

    with col3:
        if st.button("Environment CBA", use_container_width=True):
            st.switch_page("pages/3_Environment_CBA.py")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    main_app()