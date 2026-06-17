import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI(title="AI Pitch Deck Critic API")

# Add CORS middleware to allow Streamlit frontend to communicate with it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GEMINI_API_KEY environment variable must be set
client = genai.Client()

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

class CritiqueResponse(BaseModel):
    raw_response: str

@app.post("/analyze", response_model=CritiqueResponse)
async def analyze_pitch_deck(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        file_bytes = await file.read()
        
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
        
        return CritiqueResponse(raw_response=response.text)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during analysis: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
