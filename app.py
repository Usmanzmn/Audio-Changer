import streamlit as st
import os
import tempfile
import subprocess

# Voice presets (in cents)
voice_presets = {
    "Man to Woman": 500,    # +5 semitones
    "Woman to Man": -500    # -5 semitones
}

def convert_voice_sox(input_path, output_path, pitch_cents, sweeten=False):
    """
    ALWAYS convert input (MP3 or WAV) into a SoX-safe WAV first.
    This prevents exit status 2 permanently.
    """

    safe_wav = os.path.join(tempfile.gettempdir(), "safe_input.wav")

    # 🔒 Force SoX-safe WAV (PCM 16-bit, mono, 44.1kHz)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "44100",
        "-sample_fmt", "s16",
        safe_wav
    ], check=True)

    # Sanity check (debug-safe)
    subprocess.run(["sox", "--i", safe_wav], check=True)

    pitched_wav = os.path.join(tempfile.gettempdir(), "pitched.wav")

    # Pitch + tempo (stable)
    subprocess.run([
        "sox", safe_wav, pitched_wav,
        "pitch", str(pitch_cents),
        "tempo", "-s", "1.0"
    ], check=True)

    # Optional sweetening
    if sweeten:
        subprocess.run([
            "sox", pitched_wav, output_path,
            "bass", "-2",
            "treble", "+4",
            "reverb", "20"
        ], check=True)
    else:
        subprocess.run(["sox", pitched_wav, output_path], check=True)


# ---------------- UI ---------------- #

st.set_page_config(page_title="🎙️ Voice Converter")
st.title("🎙️ Voice Converter")

st.markdown(
    "Upload an **MP3 or WAV** file and convert a **male voice to female** or **female to male**.\n\n"
    "Uses **FFmpeg + SoX** with a safe audio pipeline."
)

uploaded_file = st.file_uploader("📤 Upload audio file", type=["mp3", "wav"])
voice_style = st.selectbox("🎚️ Choose Voice Conversion", list(voice_presets.keys()))
apply_sweetening = st.checkbox("✨ Make voice sound sweeter (EQ + Reverb)", value=True)

if uploaded_file:
    suffix = ".mp3" if uploaded_file.name.lower().endswith(".mp3") else ".wav"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        temp_path = tmp.name

    st.subheader("🎧 Original Audio")
    st.audio(temp_path)

    try:
        output_path = os.path.join(tempfile.gettempdir(), "converted_voice.wav")
        convert_voice_sox(
            temp_path,
            output_path,
            voice_presets[voice_style],
            sweeten=apply_sweetening
        )
    except Exception as e:
        st.error("❌ Voice conversion failed")
        st.exception(e)
        st.stop()

    st.subheader("✅ Converted Audio")
    st.audio(output_path)

    with open(output_path, "rb") as f:
        st.download_button(
            "⬇️ Download Converted Audio",
            f,
            file_name="converted_voice.wav"
        )
