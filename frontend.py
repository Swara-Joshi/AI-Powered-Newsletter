import streamlit as st
import requests

# Streamlit UI
st.title("AI-Powered Newsletter Subscription")

st.subheader("Subscribe to our AI-Powered Newsletter")

# User Input Fields
email = st.text_input("Enter your email:", placeholder="your_email@example.com")

# Dropdown for Preferences
preference_options = ["Tech News", "Finance & Markets"]
preference = st.multiselect("Choose your preferences:", preference_options)

# Submit Button
if st.button("Subscribe"):
    if email and preference:
        # Sending data to Flask backend
        response = requests.post("http://127.0.0.1:5000/subscribe", json={"email": email, "preference": ", ".join(preference)})
        if response.status_code == 200:
            st.success("Subscription successful!")
        else:
            st.error("Subscription failed. Please try again.")
    else:
        st.warning("Please enter your email and select at least one preference.")

