# ⚖️ EquiGrader AI

### Fair, Explainable, & Stress-Free Technical Interview Prep

**EquiGrader AI** is an automated practice partner designed to level the playing field for technical interviews. By leveraging **Local LLMs (Phi-3)** and **Speech Recognition (Whisper)**, it allows you to practice speaking naturally while receiving feedback based solely on your engineering logic—not your accent or grammar.

---

## 🚀 Why This Project Matters

* **Truly Fair:** Engineered prompts ignore grammatical slips or accents. If you understand the concept, you earn the points.
* **No More Mystery Scores:** Receive a detailed breakdown of rubric points hit and specific areas for improvement.
* **Privacy by Design:** Everything runs locally via **Ollama**. Your voice and data never leave your machine.

---

## ✨ Key Features

* **Dual Practice Modes:** Toggle between typing or speaking to simulate real-world pressure.
* **Intelligent Reasoning:** Powered by **Phi-3**, the system understands engineering logic rather than just scanning for keywords.
* **Modern Interface:** A clean, "Glassmorphism" styled UI built for focus.
* **Professional Architecture:** Decoupled **FastAPI** backend and **Streamlit** frontend.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | Streamlit (Python) |
| **Backend** | FastAPI (Uvicorn Server) |
| **The "Brain"** | Ollama (Phi-3 Mini Model) |
| **The "Ears"** | OpenAI Whisper |
| **Reliability** | UiPath (Automated QA Testing) |

---

## ⚙️ How to Get Started

Follow these steps to get EquiGrader AI running on your local machine.

### 1. Prerequisites
* **Python 3.10+**
* **Ollama:** [Download here](https://ollama.com/) to run the AI model locally.

### 2. Setup the AI Model
Once Ollama is installed, open your terminal and pull the model:
```bash
ollama pull phi3
```
### 3. Clone the Repository
```bash
git clone [https://github.com/YourUsername/EquiGrader-AI.git](https://github.com/YourUsername/EquiGrader-AI.git)
cd EquiGrader-AI
```
### 4. Run the Backend (The Brain)
Open a new terminal window:
```bash
cd backend
pip install -r requirements.txt
python main.py
```
Note: Wait until you see: Uvicorn running on http://127.0.0.1:8000
### 5. Run the Frontend (The Interface)
Open a second terminal window:
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## 🔮 Roadmap & Future Vision
# ##RAG Integration: Allow the AI to "read" specific textbooks for targeted exam prep.
# ##Behavioral Analysis: Use Computer Vision to provide feedback on eye contact and confidence.
# ##Expanded Disciplines: Growing the question bank to include Mechanical, Civil, and Electrical Engineering.

---

Author
Created with ❤️ and a lot of coffee by Hani Mohammad Kaif.