import streamlit as st
import os
import tempfile
import subprocess

# Voice presets (in cents)
voice_presets = {
    "Man to Woman": 500,   # +5 semitones
    "Woman to Man": -500   # -5 semitones
}

def convert_voice_sox(input_path, output_path, pitch_cents, sweeten=False):
    wav_input = input_path

    # Convert MP3 to safe PCM WAV
    if input_path.lower().endswith(".mp3"):
        wav_input = input_path.replace(".mp3", "_converted.wav")
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-ac", "1",            # mono
            "-ar", "44100",        # sample rate
            "-sample_fmt", "s16",  # 16-bit PCM
            wav_input
        ], check=True)

    # Validate WAV (prevents SoX exit status 2)
    subprocess.run(["sox", "--i", wav_input], check=True)

    # Pitch shift (with tempo for quality)
    temp_pitched = wav_input.replace(".wav", "_pitched.wav")
    subprocess.run([
        "sox", wav_input, temp_pitched,
        "pitch", str(pitch_cents),
        "tempo", "-s", "1.0"
    ], check=True)

    # Optional sweetening
    if sweeten:
        subprocess.run([
            "sox", temp_pitched, output_path,
            "bass", "-2",
            "treble", "+4",
            "reverb", "20"
        ], check=True)
    else:
        subprocess.run(["sox", temp_pitched, output_path], check=True)

# ---------------- UI ---------------- #

st.set_page_config(page_title="🎙️ Voice Converter")
st.title("🎙️ Voice Converter")
st.markdown(
    "Upload an **MP3 or WAV** file and convert a **male voice to female** or **female to male**.\n\n"
    "Optional sweetening adds EQ + reverb."
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
