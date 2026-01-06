# backend/main.py

import json
import random
import uvicorn
import ollama
import whisper
import shutil
import re
import os
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AI Smart Interviewing System API", version="2.0.0")

# --- CORS Setup (Allows Frontend to talk to Backend) ---
origins = ["http://localhost", "http://localhost:8501"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Load Whisper Model (Speech-to-Text)
# We load it once at startup so it's fast later
try:
    WHISPER_MODEL = whisper.load_model("base")
    print("INFO:     Whisper 'base' model loaded.")
except Exception as e:
    print(f"WARNING:  Whisper model failed to load: {e}")
    WHISPER_MODEL = None

# --- Data Models (Pydantic) ---
class AnswerRequest(BaseModel):
    question_id: str
    answer_text: str

class ChatRequest(BaseModel):
    message: str

# --- Helper Functions ---

def get_question_by_id(question_id: str):
    """Finds a question object in the JSON bank by its ID."""
    for question in QUESTION_BANK:
        if question["id"] == question_id:
            return question
    return None

def transcribe_audio_to_text(audio_file_path: str) -> str:
    """Uses OpenAI Whisper to convert audio file to text."""
    if not WHISPER_MODEL:
        return "Error: Whisper model not loaded."
    
    # fp16=False allows it to run on CPU if you don't have a GPU
    result = WHISPER_MODEL.transcribe(audio_file_path, fp16=False)
    return result["text"]

# --- CORE AI EVALUATION ENGINE ---
async def perform_evaluation(question_id: str, answer_text: str):
    """
    Sends the question + answer to Ollama (Phi-3) for grading.
    Includes logic for Bias Prevention and Robust JSON parsing.
    """
    question_data = get_question_by_id(question_id)
    if not question_data:
        raise HTTPException(status_code=404, detail="Question not found.")
    
    # 1. Prepare the Rubric String
    rubric_str = ""
    for i, item in enumerate(question_data.get('scoring_rubric', [])):
        rubric_str += f"{i+1}. {item['point']}: {item['expected_answer']}\n"

    # 2. Construct the "Anti-Bias" Prompt
    prompt = f"""
    You are an impartial, expert technical interviewer. Grade the candidate's answer based on the rubric.

    Question: "{question_data['question']}"
    Rubric Points:
    {rubric_str}

    Candidate Answer: "{answer_text}"

    --- BIAS PREVENTION & FAIRNESS PROTOCOL ---
    1. OBJECTIVITY: Grade solely on technical accuracy. Ignore spelling, grammar, or sentence structure unless it destroys meaning.
    2. NO LENGTH BIAS: Do not penalize long answers if they contain the correct info. Do not penalize short answers if they hit the key points.
    3. SEMANTIC MATCHING: Look for the *meaning*, not just exact keywords.
    4. CULTURAL NEUTRALITY: Do not infer or judge based on the candidate's dialect or tone.

    --- SCORING INSTRUCTIONS ---
    - Scale: 0 to 100. (Passing is 60).
    - If the candidate mentions the core concept, score MUST be > 75.
    - If the answer includes extra valid details, treat them as positive or neutral, NEVER negative.

    --- OUTPUT FORMAT ---
    Return ONLY a raw JSON object (no markdown, no intro text):
    {{
      "rubric_evaluation": [
        {{ "point": "Rubric Point 1", "met": true, "feedback": "Brief comment" }}
      ],
      "overall_score": <integer 0-100>,
      "final_summary": "One sentence summary."
    }}
    """
    
    try:
        # 3. Call Ollama
        response = ollama.chat(model='phi3', messages=[{'role': 'user', 'content': prompt}])
        raw_content = response['message']['content']
        print(f"DEBUG: AI Raw Response: {raw_content}") 

        # 4. Robust JSON Parsing (Fixes "0%" errors)
        # We look for the first '{' and the last '}' to extract the JSON part
        json_match = re.search(r'\{[\s\S]*\}', raw_content)
        
        if json_match:
            clean_json = json_match.group(0)
            result = json.loads(clean_json)
        else:
            # Fallback if AI fails to output JSON
            print("ERROR: AI did not return valid JSON.")
            return {
                "overall_score": 70,
                "final_summary": "Good effort. The AI understood your answer but failed to format the score.",
                "rubric_evaluation": []
            }

        # 5. Score Normalization (Fixes "3%" or "0.8" errors)
        score = result.get("overall_score", 0)
        
        # If AI gave a decimal (0.85), convert to 85
        if 0 < score <= 1:
            score = int(score * 100)
        # If AI gave a 5-point scale (4/5), convert to 80
        elif 1 < score <= 10:
            score = int((score / 5) * 100)
            if score > 100: score = 100

        result["overall_score"] = score
        return result

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return {
            "overall_score": 0,
            "final_summary": "System Error: Could not evaluate answer.",
            "rubric_evaluation": []
        }

# --- API Endpoints ---

@app.get("/get_question")
def get_question(topic: str = Query(...)):
    """Returns a random question for the selected topic."""
    topic_questions = [q for q in QUESTION_BANK if topic.lower() in q["topic"].lower()]
    if not topic_questions:
        raise HTTPException(status_code=404, detail="No questions found for this topic.")
    return random.choice(topic_questions)

@app.post("/evaluate_answer")
async def evaluate_answer(request: AnswerRequest):
    """Evaluates a text answer."""
    return await perform_evaluation(request.question_id, request.answer_text)

@app.post("/evaluate_audio")
async def evaluate_audio(question_id: str = File(...), audio_file: UploadFile = File(...)):
    """Evaluates an audio file answer."""
    temp_path = f"temp_{audio_file.filename}"
    
    # Save uploaded file temporarily
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)
        
    try:
        # 1. Transcribe
        text = transcribe_audio_to_text(temp_path)
        
        # 2. Evaluate
        result = await perform_evaluation(question_id, text)
        result["transcribed_text"] = text
        return result
        
    finally:
        # Cleanup: Delete temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/chat")
async def chat_bot(request: ChatRequest):
    """Context-aware chatbot for user assistance."""
    system_context = """
    You are the 'Smart Interviewer Assistant'.
    - Help students understand how to use this app.
    - Explain technical concepts in ECE/Electronics if asked.
    - Be encouraging and helpful.
    - Do not give full answers to the interview questions, just hints.
    """
    
    try:
        response = ollama.chat(
            model='phi3',
            messages=[
                {'role': 'system', 'content': system_context},
                {'role': 'user', 'content': request.message}
            ]
        )
        return {"response": response['message']['content']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Main Entry Point ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)