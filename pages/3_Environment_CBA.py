import streamlit as st

st.set_page_config(page_title="Environment CBA", page_icon="🌳")

st.title("Environment Cost Benefit Analysis Course")

st.markdown("Welcome to the Environment Cost Benefit Analysis course. Please choose which Cohort you are enrolled in to get started.")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Cohort 1 - Teacher Led", use_container_width=True):
        st.info("Coming soon!")

with col2:
    if st.button("Cohort 2 - Teacher + AI Led", use_container_width=True):
        st.info("Coming soon!")

with col3:
    if st.button("Cohort 3 - AI Led", use_container_width=True):
        st.info("Coming soon!")
