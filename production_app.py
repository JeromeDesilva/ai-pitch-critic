import streamlit as st
import os
from google import genai
from google.genai import types

# 1. THE HARD GATE: Use Streamlit's official native login wrapper
if not st.user.is_logged_in:
    st.markdown('# 💸 Welcome to AI Startup Pitch Deck Critic')
    st.markdown('Please log in to get your startup pitch deck brutally roasted.')
    
    # Streamlit handles ALL the URL code parameter parsing behind the scenes here
    if st.button('🔒 Sign in with Google', type='primary', use_container_width=True):
        st.login(provider="google")
    st.stop() 

# ====================================================================
# 2. MAIN APPLICATION WORKSPACE (Only runs if user is successfully logged in)
# ====================================================================

# Initialize Chat Memory safely
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar User Info & Logout
with st.sidebar:
    st.subheader("👤 User Profile")
    st.write(f"Logged in as:\n**{st.user.email}**")
    if st.button("🚪 Log Out", type="secondary", use_container_width=True):
        st.logout()

# Main Header
st.title("📈 AI Startup Pitch Deck Critic")
st.write("Upload your pitch deck PDF. Gemini will evaluate text, data charts, and design architecture.")

# --- File Uploader ---
uploaded_file = st.file_uploader("Choose your Pitch Deck PDF", type=["pdf"])

if uploaded_file is not None:
    if st.button("Run Global Production Analysis", type="primary", use_container_width=True):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("Error: GEMINI_API_KEY environment variable missing on cloud servers.")
            st.stop()
            
        with st.spinner("Processing Multimodal PDF Artifacts via Gemini..."):
            try:
                client = genai.Client(api_key=api_key)
                file_bytes = uploaded_file.getvalue()
                
                # Using Gemini 2.5 Flash with search grounding enabled
                system_prompt = (
                    "You are a brutal, highly successful Silicon Valley Venture Capitalist. "
                    "Analyze this startup's pitch deck. Use Google Search to verify their market claims. "
                    "Format your output exactly using the markdown split markers:\n\n"
                    "### [HOOK]\n[Critique here]\n\n"
                    "### [RED_FLAGS]\n[Critique here]\n\n"
                    "### [MOAT]\n[Critique here]\n\n"
                    "### [VERDICT]\n[YES or NO - summary]"
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                        system_prompt
                    ],
                    # Enables the live Google Search grounding tool
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )
                
                # UI Layout Parsing
                raw_text = response.text
                sections = raw_text.split("### ")
                hook, flags, moat, verdict = "N/A", "N/A", "N/A", "N/A"
                
                for sec in sections:
                    if sec.startswith("[HOOK]"): hook = sec.replace("[HOOK]", "").strip()
                    elif sec.startswith("[RED_FLAGS]"): flags = sec.replace("[RED_FLAGS]", "").strip()
                    elif sec.startswith("[MOAT]"): moat = sec.replace("[MOAT]", "").strip()
                    elif sec.startswith("[VERDICT]"): verdict = sec.replace("[VERDICT]", "").strip()

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📊 Evaluation")
                    st.info(f"**🪝 The Hook:**\n\n{hook}")
                    st.info(f"**🛡️ The Moat:**\n\n{moat}")
                with col2:
                    st.subheader("🚨 Risks & Verdict")
                    st.error(f"**Red Flags:**\n\n{flags}")
                    if "YES" in verdict.upper():
                        st.success(f"### 💰 Decision:\n{verdict}")
                    else:
                        st.warning(f"### ❌ Decision:\n{verdict}")
                        
            except Exception as e:
                st.error(f"Production Pipeline Error: {e}")

# --- Interactive Chat Memory Section ---
st.markdown("---")
st.subheader("💬 Discuss Your Pitch Deck with the VC")

# Display previous messages
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User Input
if user_message := st.chat_input("Ask a follow-up question or defend your startup..."):
    # Render user message instantly
    with st.chat_message("user"):
        st.write(user_message)
    st.session_state.chat_history.append({"role": "user", "content": user_message})
    
    # Generate VC response with memory
    with st.chat_message("assistant"):
        with st.spinner("The VC is typing..."):
            try:
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                
                # Format full context for Gemini
                chat_context = "You are the same brutal VC. Continue the discussion based on this history:\n\n"
                for msg in st.session_state.chat_history:
                    chat_context += f"{msg['role'].upper()}: {msg['content']}\n"
                
                chat_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=chat_context
                )
                
                st.write(chat_response.text)
                st.session_state.chat_history.append({"role": "assistant", "content": chat_response.text})
            except Exception as e:
                st.error(f"Chat Error: {e}")
