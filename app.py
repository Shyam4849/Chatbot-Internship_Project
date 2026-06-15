import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

# Import chatbot engine (business logic)
from chatbot import chat, log_query
from chatbot.config import STREAMLIT_TITLE, STREAMLIT_PAGE_ICON

# Optional Voice Support
try:
    from streamlit_mic_recorder import mic_recorder
    from faster_whisper import WhisperModel
    import os

    VOICE_ENABLED = True
except Exception as e:
    VOICE_ENABLED = False

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Hukum AI Terminal v2",
    page_icon=STREAMLIT_PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================================
# SESSION STATE
# ==========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_context" not in st.session_state:
    st.session_state.current_context = {}

import uuid
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================


@st.cache_resource
def load_whisper_model():
    from faster_whisper import WhisperModel
    return WhisperModel("tiny", device="cpu", compute_type="float32")


def speech_to_text(audio):
    """
    Convert browser-encoded audio (webm/ogg/opus) to text using Faster-Whisper.
    """
    if not audio or "bytes" not in audio:
        return None

    temp_filename = "temp_voice.webm"
    try:
        with open(temp_filename, "wb") as f:
            f.write(audio["bytes"])

        print(f"Audio bytes saved to {temp_filename}")

        # Load cached Whisper model
        model = load_whisper_model()

        # Transcribe audio. Supports English and Hindi auto-detection.
        segments, info = model.transcribe(temp_filename, beam_size=5)

        text = " ".join([segment.text for segment in segments]).strip()

        print("Transcribed Text:", text)
        return text if text else None

    except Exception as e:
        print("Voice pipeline error:", e)
        st.error(f"Voice Error: {e}")
        return None
    finally:
        # Clean up temp file
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except Exception as e:
                print(f"Failed to remove temp file: {e}")


# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:
    st.markdown("## 📊 Operational Notebook Targets")

    st.markdown("""
        * **Sheet Target:** `Hukum_Builders_Master_Dataset_v2.xlsx`
        * **Model Pipeline:** Live tracking across worker, job_post, reports, and material_requirement sheets.
        """)

    st.divider()

    st.markdown("### 💡 Quick Test Prompts")

    chip_1 = st.button("🔍 Find a local painter")
    chip_2 = st.button("💰 Price for 500 bags of cement")
    chip_3 = st.button("🛡️ Check risk status for Rajesh Kumar")
    chip_4 = st.button("📖 How do I post a job?")

    # ------------------------------------------------------
    # Voice Input
    # ------------------------------------------------------

    voice_query = None

    if VOICE_ENABLED:
        st.divider()
        st.markdown("### 🎤 Voice Query")

        audio = mic_recorder(
            start_prompt="🎤 Start Recording",
            stop_prompt="⏹ Stop Recording",
            just_once=True,
            use_container_width=True,
        )

        if audio:
            voice_query = speech_to_text(audio)

            if voice_query:
                st.success(f"Recognized: {voice_query}")

# ==========================================================
# HEADER
# ==========================================================

st.title(STREAMLIT_TITLE)

st.caption("Interface integrated directly with Master Excel Workbook ML Pipelines")

st.divider()

# ==========================================================
# PRESET PROMPTS
# ==========================================================

preset_query = None

if chip_1:
    preset_query = "Find a local painter"

if chip_2:
    preset_query = "Calculate price for 500 bags of cement"

if chip_3:
    preset_query = "Check risk status for Rajesh Kumar"

if chip_4:
    preset_query = "How do I post a job on the app?"

# ==========================================================
# DISPLAY CHAT HISTORY
# ==========================================================

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.caption(msg["timestamp"])

        if msg["is_html"]:
            components.html(
                msg["content"],
                height=260,
                scrolling=True,
            )
        else:
            st.markdown(msg["content"])

# ==========================================================
# USER INPUT
# ==========================================================

user_query = st.chat_input("Query the platform models directly...")

final_prompt = (
    preset_query if preset_query else voice_query if voice_query else user_query
)

# ==========================================================
# MAIN CHAT PROCESSING
# ==========================================================

if final_prompt:

    timestamp = datetime.now().strftime("%H:%M:%S")

    # -----------------------------------
    # USER MESSAGE
    # -----------------------------------

    with st.chat_message("user"):
        st.markdown(final_prompt)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": final_prompt,
            "timestamp": timestamp,
            "intent": None,
            "is_html": False,
        }
    )

    # -----------------------------------
    # PROCESS QUERY THROUGH CHATBOT ENGINE
    # -----------------------------------

    with st.spinner("Processing query..."):
        # Call the chatbot engine with session ID
        chat_result = chat(final_prompt, session_id=st.session_state.session_id)
        intent = chat_result["intent"]
        response = chat_result["response"]
        is_html_flag = chat_result["is_html"]

        # Log the query
        log_query(final_prompt, intent)

        # Update context
        st.session_state.current_context["last_intent"] = intent

    # -----------------------------------
    # ASSISTANT RESPONSE
    # -----------------------------------

    assistant_time = datetime.now().strftime("%H:%M:%S")

    with st.chat_message("assistant"):

        st.caption(f"{assistant_time} • Intent: {intent.upper()}")

        if is_html_flag:
            components.html(
                response,
                height=260,
                scrolling=True,
            )
        else:
            st.markdown(response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
            "timestamp": assistant_time,
            "intent": intent,
            "is_html": is_html_flag,
        }
    )
