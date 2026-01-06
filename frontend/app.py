import streamlit as st
import requests
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="EquiGrader AI", 
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BACKEND_URL = "http://127.0.0.1:8000"

# --- 2. PREMIUM CSS STYLING ---
st.markdown("""
    <style>
    /* Main Background & Font */
    .stApp {
        background: linear-gradient(to bottom right, #0f2027, #203a43, #2c5364);
        color: white;
    }
    
    /* Card Container */
    .css-1r6slb0, .stMarkdown, .stButton {
        font-family: 'Inter', sans-serif;
    }
    
    /* Question Card Styling */
    .question-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
        text-align: center; 
    }
    
    /* Header Gradient Text */
    .gradient-text {
        font-weight: 800;
        font-size: 3rem;
        background: -webkit-linear-gradient(45deg, #00f2fe, #4facfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    
    /* Primary Buttons */
    div.stButton > button:first-child {
        background: linear-gradient(45deg, #4facfe, #00f2fe);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 50px;
        font-weight: 700;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0, 242, 254, 0.3);
    }
    
    /* Remove default Streamlit clutter */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'current_question' not in st.session_state:
    st.session_state.current_question = None

# --- 4. ROBUST API FUNCTIONS ---
def wake_up_backend():
    """Silently pings the backend to wake it up."""
    try:
        requests.get(f"{BACKEND_URL}/docs", timeout=1)
        return True
    except:
        return False

def get_question_safe(topic):
    """Retries connection up to 5 times."""
    max_retries = 5
    for i in range(max_retries):
        try:
            res = requests.get(f"{BACKEND_URL}/get_question", params={"topic": topic}, timeout=3)
            if res.status_code == 200:
                return res.json()
        except:
            time.sleep(0.2) 
    return None

# --- 5. MAIN UI LAYOUT ---

# Top Header
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown('<h1 class="gradient-text">EquiGrader AI</h1>', unsafe_allow_html=True)
    st.caption("Fair & Explainable Technical Interview Assessment")

with c2:
    # Status Indicator
    if wake_up_backend():
        st.success("⚡ System Online")
    else:
        st.error("💤 Waking up...")

st.markdown("---")

# Main Logic
if st.session_state.current_question is None:
    # WELCOME SCREEN
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
        
        topic_map = {"Electronics (ECE)": "ECE", "Aptitude": "Aptitude"}
        selected_topic_key = st.selectbox("Choose Topic:", list(topic_map.keys()))
        
        if st.button("🚀 Start Interview Session"):
            with st.spinner("Connecting to Neural Engine..."):
                api_topic = topic_map[selected_topic_key]
                q = get_question_safe(api_topic)
                if q:
                    st.session_state.current_question = q
                    st.rerun()
                else:
                    st.error("Backend is warming up. Please click again.")

else:
    # QUESTION SCREEN
    q = st.session_state.current_question
    
    # Question Card
    st.markdown(f"""
    <div class="question-card">
        <h2 style="margin-top: 0;">{q['question']}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Interaction Area
    tab_text, tab_audio = st.tabs(["📝 **Text Answer**", "🎙️ **Voice Answer**"])
    
    with tab_text:
        with st.form("ans_form"):
            txt = st.text_area("Your Explanation:", height=200, placeholder="Type your answer here...")
            submitted = st.form_submit_button("Submit Answer")
            
            if submitted:
                if not txt:
                    st.warning("⚠️ Answer cannot be empty")
                else:
                    with st.spinner("🧠 Analyzing concept depth..."):
                        try:
                            res = requests.post(f"{BACKEND_URL}/evaluate_answer", 
                                              json={"question_id": q['id'], "answer_text": txt})
                            if res.status_code == 200:
                                data = res.json()
                                score = data['overall_score']
                                
                                # Result Card
                                st.markdown("---")
                                rc1, rc2 = st.columns([1, 3])
                                with rc1:
                                    st.metric("Score", f"{score}%", delta="Excellent" if score > 80 else "Average")
                                with rc2:
                                    st.info(f"**AI Feedback:** {data['final_summary']}")
                            else:
                                st.error("Grading failed.")
                        except Exception as e:
                            st.error(f"Error: {e}")

    with tab_audio:
        st.markdown("##### 🎙️ Voice Mode")
        audio_file = st.file_uploader("Upload Audio (WAV)", type=['wav'])
        if audio_file:
            if st.button("Analyze Audio"):
                with st.spinner("🎧 Transcribing & Grading..."):
                    try:
                        files = {"audio_file": (audio_file.name, audio_file, audio_file.type), "question_id": (None, q['id'])}
                        res = requests.post(f"{BACKEND_URL}/evaluate_audio", files=files)
                        if res.status_code == 200:
                            data = res.json()
                            st.success(f"Score: {data['overall_score']}%")
                            st.caption(f"Transcript: {data.get('transcribed_text')}")
                            st.write(data['final_summary'])
                    except:
                        st.error("Audio processing failed.")

    # Next Button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⏭️ Next Question"):
        with st.spinner("Loading next..."):
            q = get_question_safe("ECE") 
            if q:
                st.session_state.current_question = q
                st.rerun()

# --- SIDEBAR FOOTER (CREDITS) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=50)
    st.markdown("### EquiGrader AI")
    st.caption("Fair & Explainable Interview Prep")
    st.markdown("---")
    
    st.markdown("**Created by:**")
    st.markdown("### Hani Mohammad Kaif") 
    st.caption("AI Researcher & Developer")
    st.markdown("---")
    st.info("v2.0.0 • Powered by Phi-3 & Whisper")