import time
import requests
import streamlit as st
from streamlit_mic_recorder import mic_recorder

# Config
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="EquiGrader AI", 
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to bottom right, #0f2027, #203a43, #2c5364);
        color: white;
    }
    .card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
        margin-bottom: 20px;
    }
    .header-text {
        font-weight: 800;
        font-size: 3rem;
        background: -webkit-linear-gradient(45deg, #00f2fe, #4facfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    div.stButton > button:first-child {
        background: linear-gradient(45deg, #4facfe, #00f2fe);
        color: white;
        border-radius: 50px;
        font-weight: bold;
        width: 100%;
        height: 3em;
    }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Init session
if 'question_data' not in st.session_state:
    st.session_state.question_data = None

# Helpers
def check_backend():
    try:
        requests.get(f"{API_URL}/docs", timeout=1)
        return True
    except:
        return False

def fetch_question(topic):
    # Retry logic if backend is sleeping
    for _ in range(5):
        try:
            r = requests.get(f"{API_URL}/get_question", params={"topic": topic}, timeout=3)
            if r.status_code == 200:
                return r.json()
        except:
            time.sleep(0.2)
    return None

# --- Layout ---

# Header
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown('<h1 class="header-text">EquiGrader AI</h1>', unsafe_allow_html=True)
    st.caption("Fair & Explainable Technical Interview Assessment")

with c2:
    if check_backend():
        st.success("⚡ System Online")
    else:
        st.error("💤 Backend Offline")

st.markdown("---")

# Main Logic
if not st.session_state.question_data:
    # Landing Page
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h3>👋 Ready to practice?</h3>
            <p style="color: #ccc;">Select a topic below and get instant AI feedback.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # --- INTRODUCTORY EXPLANATION ---
        st.info("""
        **ℹ️ How this Interview Works:**
        You are about to participate in a simulated technical interview. 
        This is a test environment designed to evaluate your knowledge fairly.
        
        * **Evaluation:** Your answers will be graded by an AI based on a strict technical rubric.
        * **Feedback:** You will receive a detailed explanation of your score, including what you got right and what you missed.
        * **Goal:** To help you improve your technical communication and understanding.
        """)
        # --------------------------------
        
        topics = {"Electronics (ECE)": "ECE", "Aptitude": "Aptitude"}
        choice = st.selectbox("Choose Topic:", list(topics.keys()))
        
        if st.button("🚀 Start Interview"):
            with st.spinner("Connecting..."):
                topic_code = topics[choice]
                q = fetch_question(topic_code)
                if q:
                    st.session_state.question_data = q
                    st.rerun()
                else:
                    st.error("Could not fetch question. Is backend running?")

else:
    # Question Display
    q = st.session_state.question_data
    st.markdown(f"""<div class="card"><h2>{q['question']}</h2></div>""", unsafe_allow_html=True)
    
    # Input Tabs
    t1, t2 = st.tabs(["📝 Text Answer", "🎙️ Voice Answer"])
    
    # Text Tab
    with t1:
        with st.form("text_input"):
            txt_ans = st.text_area("Your Explanation:", height=200, placeholder="Type here...")
            if st.form_submit_button("Submit"):
                if not txt_ans:
                    st.warning("Please type something.")
                else:
                    # UPDATED: Changed spinner text here
                    with st.spinner("AI is evaluating..."):
                        try:
                            payload = {"question_id": q['id'], "answer_text": txt_ans}
                            res = requests.post(f"{API_URL}/evaluate_answer", json=payload)
                            if res.status_code == 200:
                                data = res.json()
                                st.divider()
                                
                                sc_col, fb_col = st.columns([1, 3])
                                sc_col.metric("Score", f"{data['overall_score']}%")
                                fb_col.info(f"**Feedback:** {data['final_summary']}")
                            else:
                                st.error("Grading failed.")
                        except Exception as e:
                            st.error(f"Error: {e}")

    # Audio Tab
    with t2:
        st.markdown("##### 🎙️ Voice Mode")
        
        audio = mic_recorder(
            start_prompt="Start Recording 🔴",
            stop_prompt="Stop Recording ⏹️",
            key="mic"
        )
        
        if audio:
            st.audio(audio['bytes'])
            if st.button("Analyze Recording"):
                # UPDATED: Changed spinner text here too
                with st.spinner("AI is evaluating..."):
                    try:
                        files = {
                            "audio_file": ("rec.wav", audio['bytes'], "audio/wav"),
                            "question_id": (None, q['id'])
                        }
                        r = requests.post(f"{API_URL}/evaluate_audio", files=files)
                        if r.status_code == 200:
                            data = r.json()
                            st.success(f"Score: {data['overall_score']}%")
                            st.caption(f"Transcript: {data.get('transcribed_text')}")
                            st.write(data['final_summary'])
                        else:
                            st.error("Audio processing failed.")
                    except Exception as e:
                        st.error(f"Conn Error: {e}")

    # Next Question
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⏭️ Next Question"):
        with st.spinner("Loading..."):
            new_q = fetch_question("ECE") 
            if new_q:
                st.session_state.question_data = new_q
                st.rerun()

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=50)
    st.markdown("### EquiGrader AI")
    st.caption("Fair & Explainable Interview Prep")
    st.markdown("---")
    
    st.markdown("**Created by:**")
    st.markdown("### Hani Mohammad Kaif") 
    st.caption("AI Researcher & Developer")
    st.markdown("---")
    st.info("v2.1 • Powered by Phi-3 & Whisper")