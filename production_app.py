import streamlit as st
import os
from google import genai
from google.genai import types

st.set_page_config(page_title="AI Startup Pitch Deck Critic", page_icon="💸", layout="wide")

st.title("💸 AI Startup Pitch Deck Critic")
st.markdown("**Upload your startup pitch deck (PDF) and get brutally roasted by an AI Silicon Valley VC.**")

SYSTEM_PROMPT = """You are a brutal, hyper-critical Silicon Valley Venture Capitalist. 
You review pitch decks and tear them apart if they aren't flawless. 
You must analyze the provided PDF pitch deck (which includes slides, charts, and design layouts).
Your response MUST strictly separate the critique into four sections using the exact string markers below.
Do not include any text outside of these sections. Do not use any markdown formatting on the markers themselves.

### [HOOK]
(Evaluate the opening. Does it grab attention immediately? Or is it boring?)

### [RED_FLAGS]
(Identify all weaknesses, unrealistic assumptions, poor design choices, or missing data.)

### [MOAT]
(Analyze their competitive advantage. Do they actually have one, or are they easily replaceable?)

### [VERDICT]
(Give your final, unvarnished decision: Fund or Pass, and why.)

Ensure the markers are exactly as specified above so the UI can parse them correctly.
"""

# Check for GEMINI_API_KEY (handles both local env vars and Streamlit Cloud secrets)
if "GEMINI_API_KEY" not in os.environ and "GEMINI_API_KEY" not in st.secrets:
    st.error("Missing GEMINI_API_KEY! Please set it in your environment variables or Streamlit secrets.")
    st.stop()

# Initialize Gemini Client. It will automatically pick up GEMINI_API_KEY from os.environ or st.secrets
# However, to be safe with Streamlit secrets dict, let's pass it directly if it's in secrets and not in environ
api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

uploaded_file = st.file_uploader("Upload Pitch Deck (PDF only)", type=["pdf"])

if uploaded_file is not None:
    st.info("File uploaded successfully. Click the button below to get your critique.")
    
    if st.button("Roast My Pitch Deck"):
        with st.spinner("The VC is reviewing your deck... (This might take a minute or two)"):
            try:
                file_bytes = uploaded_file.getvalue()
                
                # Send raw bytes to Gemini natively
                document_part = types.Part.from_bytes(data=file_bytes, mime_type="application/pdf")
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        document_part, 
                        "Analyze this pitch deck and provide your brutal VC critique."
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.7,
                    )
                )
                
                raw_text = response.text
                
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
                    st.header("🎣 The Hook")
                    st.write(hook if hook else "No comments on the hook.")
                    
                    st.header("🚩 Red Flags")
                    st.error(red_flags if red_flags else "Surprisingly, no red flags found.")
                    
                    st.header("🏰 The Moat")
                    st.info(moat if moat else "No moat detected. You're defenseless.")
                    
                    st.header("⚖️ The Verdict")
                    st.success(verdict if verdict else "The VC stormed out without a verdict.")
                    
            except Exception as e:
                st.error(f"An unexpected error occurred during analysis: {str(e)}")
