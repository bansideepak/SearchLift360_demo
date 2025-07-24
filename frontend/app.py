import streamlit as st
import httpx
import os

# --- Configuration ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001/chat")

# --- Streamlit Page Setup ---
st.set_page_config(page_title="SearchLift360 Chat", layout="wide")

st.title("🤖 SearchLift360")
st.caption("I can search for products and hotels.")

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! How can I assist you today? Try asking: 'Find hotels in Hyderabad' or 'Are there any vintage pink shoes?'"}
    ]

# --- UI Rendering ---

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- User Input and Backend Communication ---

if prompt := st.chat_input("What are you looking for?"):
    # Initialize full_response to prevent UnboundLocalError in case of unexpected exceptions
    full_response = ""
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response from backend
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # Use a context manager for the client
            with httpx.Client(timeout=120.0) as client:
                payload = {"prompt": prompt, "history": st.session_state.messages}
                
                with st.spinner("Thinking..."):
                    response = client.post(BACKEND_URL, json=payload)

                if response.status_code == 200:
                    api_response = response.json()
                    full_response = api_response.get("response", "I received a response, but it was empty.")
                else:
                    # Gracefully handle non-JSON error responses from the server
                    try:
                        error_details = response.json().get("detail", response.text)
                    except Exception:
                        error_details = response.text or "No error details could be retrieved from the server."
                    full_response = f"**Error from API:**\n\n> Status: `{response.status_code}`\n\n> Details: `{error_details}`"
            
            if full_response:
                message_placeholder.markdown(full_response)

        except httpx.ConnectError as e:
            full_response = f"**Connection Error**\n\nI couldn't connect to the backend at `{BACKEND_URL}`. Is the server running?"
            message_placeholder.error(full_response)
        except Exception as e:
            full_response = f"An unexpected error occurred: {e}"
            message_placeholder.error(full_response)

    # Add assistant response to chat history only if a response was generated
    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})
