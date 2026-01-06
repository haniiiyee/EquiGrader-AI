import json
import random
import uvicorn
import ollama
import whisper
import shutil
import re
import os
import io
import numpy as np
# New imports
import librosa
from pydub import AudioSegment
import firebase_admin
from firebase_admin import credentials, firestore

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AI Smart Interviewer API", version="2.1.0")

# --- CORS Setup ---
origins = ["http://localhost", "http://localhost:8501"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Firebase Initialization (Placeholder) ---
# NOTE: To use Firebase, you must download your serviceAccountKey.json from Firebase Console
# and place it in the 'backend' folder.
try:
    if os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("INFO:     Firebase initialized successfully.")
    else:
        print("WARNING:  serviceAccountKey.json not found. Firebase features disabled.")
        db = None
except Exception as e:
    print(f"WARNING:  Firebase init failed: {e}")
    db = None

# --- Global Data Loading ---
def load_question_bank():
    try:
        with open("questions.json", "r") as f:
            print("INFO:     Loading question bank...")
            return json.load(f)
    except Exception as e:
        print(f"ERROR:    Could not load questions.json: {e}")
        return []

QUESTION_BANK = load_question_bank()

# Load Whisper Model
try:
    WHISPER_MODEL = whisper.load_model("base")
    print("INFO:     Whisper 'base' model loaded.")
except Exception as e:
    print(f"WARNING:  Whisper model failed to load: {e}")
    WHISPER_MODEL = None

# --- Data Models ---
class AnswerRequest(BaseModel):
    question_id: str
    answer_text: str

class ChatRequest(BaseModel):
    message: str

# --- Helper Functions ---
def get_question_by_id(question_id: str):
    for question in QUESTION_BANK:
        if question["id"] == question_id:
            return question
    return None

def transcribe_audio_to_text(audio_file_path: str) -> str:
    """Uses OpenAI Whisper to convert audio file to text."""
    if not WHISPER_MODEL:
        return "Error: Whisper model not loaded."
    
    # We can use librosa here to load audio if we want to do pre-processing
    # y, sr = librosa.load(audio_file_path) 
    # But Whisper handles file paths directly very well.
    
    result = WHISPER_MODEL.transcribe(audio_file_path, fp16=False)
    return result["text"]

# --- CORE AI EVALUATION ENGINE ---
async def perform_evaluation(question_id: str, answer_text: str):
    question_data = get_question_by_id(question_id)
    if not question_data:
        raise HTTPException(status_code=404, detail="Question not found.")
    
    rubric_str = ""
    for i, item in enumerate(question_data.get('scoring_rubric', [])):
        rubric_str += f"{i+1}. {item['point']}: {item['expected_answer']}\n"

    prompt = f"""
    You are an impartial, expert technical interviewer. Grade the candidate's answer based on the rubric.

    Question: "{question_data['question']}"
    Rubric Points:
    {rubric_str}

    Candidate Answer: "{answer_text}"

    --- SCORING INSTRUCTIONS ---
    - Scale: 0 to 100. (Passing is 60).
    - If the candidate mentions the core concept, score MUST be > 75.
    - Ignore minor grammar issues.

    --- OUTPUT FORMAT ---
    Return ONLY a raw JSON object:
    {{
      "rubric_evaluation": [
        {{ "point": "Rubric Point 1", "met": true, "feedback": "Brief comment" }}
      ],
      "overall_score": <integer 0-100>,
      "final_summary": "One sentence summary."
    }}
    """
    
    try:
        response = ollama.chat(model='phi3', messages=[{'role': 'user', 'content': prompt}])
        raw_content = response['message']['content']
        
        json_match = re.search(r'\{[\s\S]*\}', raw_content)
        if json_match:
            result = json.loads(json_match.group(0))
        else:
            return {
                "overall_score": 70,
                "final_summary": "AI graded but failed to format JSON.",
                "rubric_evaluation": []
            }

        # Normalize Score
        score = result.get("overall_score", 0)
        if 0 < score <= 1: score = int(score * 100)
        elif 1 < score <= 10: score = int((score / 5) * 100)
        if score > 100: score = 100
        result["overall_score"] = score
        
        # --- Firebase Logging (Optional) ---
        if db:
            try:
                # Save result to Firestore
                doc_ref = db.collection('interviews').document()
                doc_ref.set({
                    'question_id': question_id,
                    'answer': answer_text,
                    'score': score,
                    'timestamp': firestore.SERVER_TIMESTAMP
                })
            except Exception as e:
                print(f"Firebase error: {e}")

        return result

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return {
            "overall_score": 0,
            "final_summary": "System Error.",
            "rubric_evaluation": []
        }

# --- API Endpoints ---

@app.get("/get_question")
def get_question(topic: str = Query(...)):
    topic_questions = [q for q in QUESTION_BANK if topic.lower() in q["topic"].lower()]
    if not topic_questions:
        raise HTTPException(status_code=404, detail="No questions found.")
    return random.choice(topic_questions)

@app.post("/evaluate_answer")
async def evaluate_answer(request: AnswerRequest):
    return await perform_evaluation(request.question_id, request.answer_text)

@app.post("/evaluate_audio")
async def evaluate_audio(question_id: str = File(...), audio_file: UploadFile = File(...)):
    temp_path = f"temp_{audio_file.filename}"
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)
        
    try:
        # Example pydub usage: Check duration
        audio = AudioSegment.from_file(temp_path)
        duration_seconds = len(audio) / 1000
        print(f"Audio duration: {duration_seconds} seconds")

        text = transcribe_audio_to_text(temp_path)
        result = await perform_evaluation(question_id, text)
        result["transcribed_text"] = text
        return result
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/chat")
async def chat_bot(request: ChatRequest):
    system_context = "You are the 'EquiGrader AI' assistant. Help students."
    try:
        response = ollama.chat(
            model='phi3',
            messages=[{'role': 'system', 'content': system_context},
                      {'role': 'user', 'content': request.message}]
        )
        return {"response": response['message']['content']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)