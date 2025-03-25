import streamlit as st
import requests

# FastAPI Backend URL
# BACKEND_URL = "http://127.0.0.1:8000"

st.title("📩 AI-Powered News Subscription")
st.subheader("Get AI-generated news summaries delivered to your inbox!")

# Subscription Form
email = st.text_input("Enter your email:")
category = st.selectbox("Select news category:", ["technology", "business"])

if st.button("Subscribe"):
    response = requests.post(f"{BACKEND_URL}/subscribe/", params={"email": email, "category": category})
    if response.status_code == 200:
        st.success("Successfully subscribed! Check your email for daily updates.")
    else:
        st.error("Subscription failed. Try again.")

st.markdown("---")
st.markdown("Powered by OpenAI & NewsAPI | Built with ❤️ using FastAPI & Streamlit")

