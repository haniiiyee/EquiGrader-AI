import os
import json
import random
import shutil
import re
import numpy as np

# Audio & AI libs
import whisper
import ollama
import librosa
from pydub import AudioSegment

# Web Server libs
import uvicorn
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Database (Optional)
import firebase_admin
from firebase_admin import credentials, firestore

app = FastAPI(title="EquiGrader AI API", version="2.2")

# 1. Setup CORS (Allows frontend to talk to us)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Database Connection (Safe Mode)
db = None
try:
    if os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase connected successfully.")
    else:
        print("Note: serviceAccountKey.json missing. Running without database.")
except Exception as e:
    print(f"Database init failed: {e}")

# 3. Load Data
questions_db = []
try:
    with open("questions.json", "r") as f:
        questions_db = json.load(f)
    print(f"Loaded {len(questions_db)} questions.")
except Exception as e:
    print("Error loading questions:", e)

# 4. Load AI Models
whisper_model = None
try:
    whisper_model = whisper.load_model("base")
    print("Whisper speech engine ready.")
except:
    print("Warning: Whisper failed to load.")

# --- Request Models ---
class AnswerReq(BaseModel):
    question_id: str
    answer_text: str

class ChatReq(BaseModel):
    message: str

# --- Core Functions ---

def find_question(qid):
    for q in questions_db:
        if q["id"] == qid:
            return q
    return None

def get_transcription(file_path):
    """Converts audio file to text using Whisper."""
    if not whisper_model:
        return "Error: Model not loaded"
    
    # We allow CPU usage with fp16=False
    result = whisper_model.transcribe(file_path, fp16=False)
    return result["text"]

# NOTE: We use standard 'def' (not async) for heavy AI tasks 
# to prevent blocking the server heartbeat.
def grade_with_llm(qid, user_answer):
    q_data = find_question(qid)
    if not q_data:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Format the rubric for the AI
    rubric_text = ""
    for idx, item in enumerate(q_data.get('scoring_rubric', [])):
        rubric_text += f"{idx+1}. {item['point']}: {item['expected_answer']}\n"

    # The Logic Prompt (Anti-Bias)
    system_prompt = f"""
    You are an impartial technical interviewer. Grade the candidate based on this rubric.
    
    Question: "{q_data['question']}"
    Rubric:
    {rubric_text}
    
    Candidate Answer: "{user_answer}"
    
    Grading Rules:
    1. Score from 0 to 100. (60 is a pass).
    2. Focus on TECHNICAL CORRECTNESS only. Ignore grammar/accent.
    3. If they hit the key concepts, score > 75.
    4. Do not be too harsh on short answers if they are accurate.
    
    Return JSON only:
    {{
      "rubric_evaluation": [
        {{ "point": "Point Name", "met": true, "feedback": "note" }}
      ],
      "overall_score": 0,
      "final_summary": "summary here"
    }}
    """

    try:
        # Ask Ollama
        res = ollama.chat(model='phi3', messages=[{'role': 'user', 'content': system_prompt}])
        ai_output = res['message']['content']
        print(f"AI Response: {ai_output}") 

        # Find JSON in the response
        match = re.search(r'\{[\s\S]*\}', ai_output)
        if match:
            data = json.loads(match.group(0))
        else:
            return {
                "overall_score": 70, 
                "final_summary": "AI error: output format invalid", 
                "rubric_evaluation": []
            }

        # Fix score scaling issues (e.g. 0.8 -> 80)
        score = data.get("overall_score", 0)
        if score <= 1: score = int(score * 100)
        elif score <= 10: score = int((score/5)*100)
        
        if score > 100: score = 100
        data["overall_score"] = score
        
        return data

    except Exception as e:
        print(f"Grading failed: {e}")
        return {"overall_score": 0, "final_summary": "Server error", "rubric_evaluation": []}

# --- API Routes ---

@app.get("/get_question")
def route_get_question(topic: str = Query(...)):
    # Filter questions by topic
    filtered = [q for q in questions_db if topic.lower() in q["topic"].lower()]
    if not filtered:
        raise HTTPException(status_code=404, detail="No questions found")
    return random.choice(filtered)

@app.post("/evaluate_answer")
def route_eval_text(req: AnswerReq):
    # Runs in threadpool to avoid blocking
    return grade_with_llm(req.question_id, req.answer_text)

@app.post("/evaluate_audio")
def route_eval_audio(question_id: str = File(...), audio_file: UploadFile = File(...)):
    temp_filename = f"temp_{audio_file.filename}"
    
    # Save file to disk
    with open(temp_filename, "wb") as f:
        shutil.copyfileobj(audio_file.file, f)
        
    try:
        # Optional: Use pydub to check audio length (demonstrating library usage)
        # audio = AudioSegment.from_file(temp_filename)
        # print(f"Audio Length: {len(audio)}ms")

        # Process
        text = get_transcription(temp_filename)
        result = grade_with_llm(question_id, text)
        result["transcribed_text"] = text
        return result
    finally:
        # Cleanup
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@app.post("/chat")
def route_chat(req: ChatReq):
    context = "You are EquiGrader AI assistant. Help students with app usage or tech concepts."
    try:
        res = ollama.chat(model='phi3', messages=[
            {'role': 'system', 'content': context},
            {'role': 'user', 'content': req.message}
        ])
        return {"response": res['message']['content']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)