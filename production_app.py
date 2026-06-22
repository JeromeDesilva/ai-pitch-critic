import streamlit as st
import os
from google import genai
from google.genai import types

st.set_page_config(page_title="AI Startup Pitch Deck Critic", page_icon="💸", layout="wide")

# User Authentication Safe Helper
def check_is_logged_in():
    user_obj = getattr(st, "user", getattr(st, "experimental_user", None))
    if user_obj is not None:
        if isinstance(user_obj, dict):
            return user_obj.get("is_logged_in", False)
        return getattr(user_obj, "is_logged_in", False)
    return False

def get_user_info(key, default):
    user_obj = getattr(st, "user", getattr(st, "experimental_user", None))
    if user_obj is not None:
        if isinstance(user_obj, dict):
            return user_obj.get(key, default)
        return getattr(user_obj, key, default)
    return default

if not check_is_logged_in():
    st.title("💸 Welcome to AI Startup Pitch Deck Critic")
    st.markdown("Please log in to get your startup pitch deck brutally roasted.")
    if hasattr(st, "login"):
        try:
            st.login(provider="google")
        except Exception as e:
            st.error(f"Authentication setup is incomplete: {str(e)}")
            st.info("If you are the developer, please ensure 'Authlib' is installed and Streamlit Cloud Authentication is properly configured in your app secrets.")
    else:
        st.warning("Authentication is not supported in this environment.")
    st.stop()

# Sidebar User Profile
with st.sidebar:
    st.header("👤 Profile")
    st.write(f"**Name:** {get_user_info('name', 'Guest')}")
    st.write(f"**Email:** {get_user_info('email', 'guest@example.com')}")
    if hasattr(st, "logout"):
        st.logout()

st.title("💸 AI Startup Pitch Deck Critic")
st.markdown("**Upload your startup pitch deck (PDF) and get brutally roasted by an AI Silicon Valley VC.**")

SYSTEM_PROMPT = """You are a brutal, hyper-critical Silicon Valley Venture Capitalist. 
You review pitch decks and tear them apart if they aren't flawless. 
You must analyze the provided PDF pitch deck (which includes slides, charts, and design layouts).
Use your Google Search tool to actively verify the startup's market claims and explicitly check if competitors already exist in India for their specific niche.

For your FIRST response (the initial pitch deck review), your response MUST strictly separate the critique into four sections using the exact string markers below.
Do not include any text outside of these sections. Do not use any markdown formatting on the markers themselves.

### [HOOK]
(Evaluate the opening. Does it grab attention immediately? Or is it boring?)

### [RED_FLAGS]
(Identify all weaknesses, unrealistic assumptions, poor design choices, missing data, and flag any existing Indian competitors found via search.)

### [MOAT]
(Analyze their competitive advantage. Do they actually have one, or are they easily replaceable?)

### [VERDICT]
(Give your final, unvarnished decision: Fund or Pass, and why.)

Ensure the markers are exactly as specified above so the UI can parse them correctly in the first turn.

For subsequent follow-up questions from the founder, stay in your brutal VC persona, address their questions or defenses, and do NOT use the section markers.
"""

# Check for GEMINI_API_KEY
if "GEMINI_API_KEY" not in os.environ and "GEMINI_API_KEY" not in st.secrets:
    st.error("Missing GEMINI_API_KEY! Please set it in your environment variables or Streamlit secrets.")
    st.stop()

api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "critique_done" not in st.session_state:
    st.session_state.critique_done = False

uploaded_file = st.file_uploader("Upload Pitch Deck (PDF only)", type=["pdf"])

if uploaded_file is not None and not st.session_state.critique_done:
    st.info("File uploaded successfully. Click the button below to get your critique.")
    
    if st.button("Roast My Pitch Deck"):
        with st.spinner("The VC is reviewing your deck... (This might take a minute or two)"):
            try:
                file_bytes = uploaded_file.getvalue()
                
                # Send raw bytes to Gemini natively
                document_part = types.Part.from_bytes(data=file_bytes, mime_type="application/pdf")
                prompt = "Analyze this pitch deck and provide your brutal VC critique."
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        document_part, 
                        prompt
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.7,
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )
                
                raw_text = response.text
                
                # Add to chat history
                st.session_state.chat_history.append({"role": "user", "parts": [document_part, types.Part.from_text(prompt)]})
                st.session_state.chat_history.append({"role": "model", "parts": [types.Part.from_text(raw_text)]})
                st.session_state.critique_done = True
                st.rerun()
                    
            except Exception as e:
                st.error(f"An unexpected error occurred during analysis: {str(e)}")

# Display Chat History and Critique Dashboard if critique is done
if st.session_state.critique_done:
    st.header("VC Dashboard")
    
    # We display the initial critique from the first model message
    # The first model message is at index 1 in the chat history
    if len(st.session_state.chat_history) > 1:
        first_model_message = st.session_state.chat_history[1]["parts"][0].text
        raw_text = first_model_message
        
        def extract_section(text, start_marker, next_marker=None):
            try:
                start_idx = text.index(start_marker) + len(start_marker)
                if next_marker and next_marker in text:
                    end_idx = text.index(next_marker)
                    return text[start_idx:end_idx].strip()
                else:
                    return text[start_idx:].strip()
            except ValueError:
                return ""

        hook = extract_section(raw_text, "### [HOOK]", "### [RED_FLAGS]")
        red_flags = extract_section(raw_text, "### [RED_FLAGS]", "### [MOAT]")
        moat = extract_section(raw_text, "### [MOAT]", "### [VERDICT]")
        verdict = extract_section(raw_text, "### [VERDICT]")
        
        if not any([hook, red_flags, moat, verdict]):
            st.warning("The VC went off-script! Here's the raw feedback:")
            st.write(raw_text)
        else:
            st.subheader("🎣 The Hook")
            st.write(hook if hook else "No comments on the hook.")
            
            st.subheader("🚩 Red Flags")
            st.error(red_flags if red_flags else "Surprisingly, no red flags found.")
            
            st.subheader("🏰 The Moat")
            st.info(moat if moat else "No moat detected. You're defenseless.")
            
            st.subheader("⚖️ The Verdict")
            st.success(verdict if verdict else "The VC stormed out without a verdict.")
            
    st.divider()
    st.header("Argue with the VC")
    
    # Render chat messages (skipping the first turn which is the document upload and initial critique)
    for i in range(2, len(st.session_state.chat_history)):
        message = st.session_state.chat_history[i]
        role = message["role"]
        # Convert user to human, model to ai for st.chat_message
        st_role = "user" if role == "user" else "assistant"
        with st.chat_message(st_role):
            # Render all text parts
            for part in message["parts"]:
                if hasattr(part, "text") and part.text:
                    st.markdown(part.text)

    # Chat input
    if user_input := st.chat_input("Defend your startup or ask how to fix the red flags..."):
        # Append user message
        st.session_state.chat_history.append({"role": "user", "parts": [types.Part.from_text(user_input)]})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
            
        with st.chat_message("assistant"):
            with st.spinner("The VC is typing..."):
                try:
                    # Construct contents for the API
                    # The google-genai SDK accepts a list of Content objects for multi-turn chats
                    contents = []
                    for msg in st.session_state.chat_history:
                        contents.append(types.Content(role=msg["role"], parts=msg["parts"]))
                        
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.7,
                            tools=[types.Tool(google_search=types.GoogleSearch())]
                        )
                    )
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "model", "parts": [types.Part.from_text(response.text)]})
                except Exception as e:
                    st.error(f"Error: {e}")
