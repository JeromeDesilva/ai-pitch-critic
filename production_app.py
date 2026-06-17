import streamlit as st
import requests

API_URL = "http://localhost:8000/analyze"

st.set_page_config(page_title="AI Startup Pitch Deck Critic", page_icon="💸", layout="wide")

st.title("💸 AI Startup Pitch Deck Critic")
st.markdown("**Upload your startup pitch deck (PDF) and get brutally roasted by an AI Silicon Valley VC.**")

uploaded_file = st.file_uploader("Upload Pitch Deck (PDF only)", type=["pdf"])

if uploaded_file is not None:
    st.info("File uploaded successfully. Click the button below to get your critique.")
    
    if st.button("Roast My Pitch Deck"):
        with st.spinner("The VC is reviewing your deck... (This might take a minute or two)"):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                response = requests.post(API_URL, files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    raw_text = data.get("raw_response", "")
                    
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
                        
                else:
                    st.error(f"Error from backend: {response.status_code} - {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Failed to connect to the backend. Make sure the FastAPI backend is running on http://localhost:8000")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
