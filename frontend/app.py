import streamlit as st
import requests
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="EquiGrader AI", 
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BACKEND_URL = "http://127.0.0.1:8000"

# --- 2. CSS STYLING ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(to bottom right, #0f2027, #203a43, #2c5364); color: white; }
    .question-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center; 
    }
    div.stButton > button:first-child {
        background: linear-gradient(45deg, #4facfe, #00f2fe);
        color: white; border: none; border-radius: 50px; font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'current_question' not in st.session_state:
    st.session_state.current_question = None

# --- 4. API HELPER ---
def get_question_safe(topic):
    try:
        res = requests.get(f"{BACKEND_URL}/get_question", params={"topic": topic}, timeout=3)
        if res.status_code == 200: return res.json()
    except: return None
    return None

# --- 5. MAIN UI ---
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("<h1>EquiGrader AI</h1>", unsafe_allow_html=True)
    st.caption("Fair & Explainable Technical Interview Assessment")

with c2:
    try:
        if requests.get(f"{BACKEND_URL}/docs", timeout=1).status_code == 200:
            st.success("⚡ System Online")
    except:
        st.error("💤 Backend Offline")

st.markdown("---")

if st.session_state.current_question is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("👋 Select a topic to begin.")
        topic_map = {"Electronics (ECE)": "ECE", "Aptitude": "Aptitude"}
        selected_key = st.selectbox("Choose Topic:", list(topic_map.keys()))
        
        if st.button("🚀 Start Interview"):
            q = get_question_safe(topic_map[selected_key])
            if q:
                st.session_state.current_question = q
                st.rerun()
            else:
                st.error("Backend Error.")
else:
    q = st.session_state.current_question
    st.markdown(f"""<div class="question-card"><h2>{q['question']}</h2></div>""", unsafe_allow_html=True)
    
    tab_text, tab_audio = st.tabs(["📝 **Text Answer**", "🎙️ **Voice Answer**"])
    
    with tab_text:
        with st.form("ans_form"):
            txt = st.text_area("Your Answer:")
            if st.form_submit_button("Submit"):
                try:
                    res = requests.post(f"{BACKEND_URL}/evaluate_answer", json={"question_id": q['id'], "answer_text": txt})
                    if res.status_code == 200:
                        data = res.json()
                        st.success(f"Score: {data['overall_score']}%")
                        st.write(f"**Feedback:** {data['final_summary']}")
                except Exception as e:
                    st.error(f"Error: {e}")

    with tab_audio:
        st.markdown("##### 🎙️ Record Answer")
        # --- STREAMLIT-MIC-RECORDER INTEGRATION ---
        audio = mic_recorder(
            start_prompt="Start Recording 🔴",
            stop_prompt="Stop Recording ⏹️",
            key="recorder"
        )
        
        if audio:
            st.audio(audio['bytes'])
            if st.button("Analyze Recording"):
                with st.spinner("Processing..."):
                    try:
                        files = {"audio_file": ("rec.wav", audio['bytes'], "audio/wav"), "question_id": (None, q['id'])}
                        res = requests.post(f"{BACKEND_URL}/evaluate_audio", files=files)
                        if res.status_code == 200:
                            data = res.json()
                            st.success(f"Score: {data['overall_score']}%")
                            st.info(f"Transcript: {data.get('transcribed_text')}")
                            st.write(data['final_summary'])
                    except Exception as e:
                        st.error(f"Error: {e}")

    if st.button("⏭️ Next Question"):
        q = get_question_safe("ECE") 
        if q:
            st.session_state.current_question = q
            st.rerun()

# --- SIDEBAR CREDITS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=50)
    st.markdown("### EquiGrader AI")
    st.markdown("**Created by:** Hani Mohammad Kaif") 
    st.info("v2.1.0 • Powered by Phi-3, Whisper, Librosa, & Firebase")