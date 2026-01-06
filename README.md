⚖️ EquiGrader AI
Fair, Explainable, & Stress-Free Technical Interview Prep
Hi there! Welcome to EquiGrader AI. 👋
I built this project because technical interviews can be intimidating and, sometimes, unfair. We've all been there—knowing the answer but struggling to explain it, or worrying that a minor grammar mistake might cost us the job.
EquiGrader AI is my solution to that. It's an automated interview platform designed to be your unbiased practice partner. It uses Generative AI (Phi-3) to understand your answers and Speech Recognition (Whisper) so you can practice speaking naturally. The goal? To give every ECE student a fair shot at mastering their technical concepts with clear, constructive feedback.

Why This Project Matters
It's Fair: I engineered the AI prompts to strictly ignore grammatical errors or accents. If you know the engineering concept, you get the points. Period.
It Explains "Why": Getting a "7/10" score is useless if you don't know what you missed. This tool tells you exactly why you got that score and what specific rubric points you hit or missed.
It's Private: Unlike many online tools, this uses Local LLMs (Ollama). Your voice and data never leave your computer.

Key Features
Full Stack Design: A clean separation between the Streamlit frontend (the face) and the FastAPI backend (the brain).
Voice-First: Uses OpenAI Whisper to let you answer verbally, simulating a real Zoom or in-person interview.
Intelligent Grading: It doesn't just look for keywords. It evaluates your answer against a deep technical rubric to check for core understanding.
Bias Prevention: The system is explicitly instructed to be objective, focusing solely on technical accuracy.

Under the Hood (Tech Stack)
I chose these technologies to build a robust, modern application:
Frontend: Streamlit, Python (For a clean, responsive User Interface)
Backend: FastAPI, Uvicorn (For high-performance API handling)
The Brains: Ollama (Phi-3 Mini) & OpenAI Whisper (Base model)
Data: JSON-based Question Bank (Easy to expand and maintain)
Quality Assurance: Automated testing via UiPath to ensure stability.

How to Run It Locally
Want to try it out? Follow these steps to get it running on your machine.

1. Prerequisites
You'll need a few things installed first:
Python 3.10+
Ollama (This runs the AI model).
Once Ollama is installed, open your terminal and pull the brain:
ollama pull phi3

2. Get the Code
git clone [https://github.com/YourUsername/EquiGrader-AI.git](https://github.com/YourUsername/EquiGrader-AI.git)
cd EquiGrader-AI

3. Start the Backend (The Brain)
Open a terminal window and run:
cd backend
pip install -r requirements.txt
python main.py
Wait a moment until you see: "Uvicorn running on https://www.google.com/search?q=http://127.0.0.1:8000"

4. Start the Frontend (The Interface)
Open a new terminal window and run:
cd frontend
pip install -r requirements.txt
streamlit run app.py
The app should pop up in your browser automatically!

What's Next?
I have big plans to make this even better:
RAG Integration: So the AI can "read" textbooks and ask questions from specific chapters.
Computer Vision: Adding optional eye-tracking to help you practice maintaining eye contact (without being creepy about it!).
More Subjects: Expanding beyond ECE to Mechanical and Civil Engineering topics.
Created with by: Hani Mohammad Kaif