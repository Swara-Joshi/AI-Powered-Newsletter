import streamlit as st
import requests

# FastAPI Backend URL
BACKEND_URL = "http://127.0.0.1:8000"

# Ask for the OpenAI API key
openai_api_key = st.text_input("Enter your OpenAI API key:")

# Check if the OpenAI API key is provided
if openai_api_key:
    st.title("📩 AI-Powered News Subscription")
    st.subheader("Get AI-generated news summaries delivered to your inbox!")

    # Subscription Form
    email = st.text_input("Enter your email:")
    category = st.selectbox("Select news category:", ["technology", "business"])

    # Subscribe button
    if st.button("Subscribe"):
        # Make the POST request to FastAPI backend
        response = requests.post(f"{BACKEND_URL}/subscribe/", params={"email": email, "category": category})
        
        if response.status_code == 200:
            # Show success message
            st.success("Successfully subscribed! Check your email for daily updates.")
        else:
            # Show error message
            st.error("Subscription failed. Try again.")

   