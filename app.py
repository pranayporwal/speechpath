import os
import tempfile
import librosa
import soundfile as sf
import google.generativeai as genai
from difflib import SequenceMatcher

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from transcribe_test import load_model, transcribe



# Create FastAPI app
app = FastAPI()

# CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load Wav2Vec2 ONCE when the server starts

processor, model = load_model()

# --------------------------------------------------
# Configure Gemini
# --------------------------------------------------

gemini_api_key = os.environ.get("GEMINI_API_KEY")

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

    gemini_model = genai.GenerativeModel(
        "gemini-3.6-flash"
    )
else:
    gemini_model = None
    
def preprocess_audio(input_path):

    audio, sample_rate = librosa.load(
        input_path,
        sr=16000,
        mono=True
    )

    

    # Normalize volume
    max_amplitude = max(abs(audio))

    if max_amplitude > 0:
        audio = audio / max_amplitude

    # Save processed audio
    processed_path = input_path.replace(
        ".wav",
        "_processed.wav"
    )

    sf.write(
        processed_path,
        audio,
        16000
    )

    return processed_path

# Word-level similarity

def calculate_score(transcript, expected_phrase):
    transcript_words = transcript.lower().split()
    expected_words = expected_phrase.lower().split()

    if not expected_words:
        return 0

    similarity = SequenceMatcher(
        None,
        transcript_words,
        expected_words
    ).ratio()

    return round(similarity * 100)

# --------------------------------------------------
# Generate pronunciation feedback
# --------------------------------------------------

def generate_feedback(
    transcript,
    expected_phrase,
    score
):

    if gemini_model is None:
        return "Keep practicing that phrase!"

    prompt = f"""
The user was asked to say: "{expected_phrase}"

Their actual speech was transcribed as:
"{transcript}"

Their pronunciation match score was {score}/100.

As a supportive speech therapist, give one short
1-2 sentence corrective tip focused on what they
likely mispronounced.

Be encouraging, simple, and not clinical.
Do not mention that you are an AI.
"""

    try:
        print("Sending request to Gemini...")

        response = gemini_model.generate_content(
            prompt
        )
        print("Gemini response received.")

        if response.text:
            return response.text.strip()

        return "Keep practicing that phrase!"

    except Exception as e:

        print("Gemini feedback error:", e)

        return "Keep practicing that phrase!"


# POST /assess

@app.post("/assess")

async def assess(
    audio: UploadFile = File(...),
    expected_phrase: str = Form(...)
):
    print("Received audio:", audio.filename)
    print("Expected phrase:", expected_phrase)

    temp_path = None
    processed_path = None

    try:
        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        ) as temp_file:

            temp_path = temp_file.name

            # Save uploaded audio
            content = await audio.read()
            print("Received file size:", len(content), "bytes")
            temp_file.write(content)

        processed_path = preprocess_audio(

            temp_path
        )


        # Transcribe using the already-loaded model
        transcript = transcribe(
            processed_path,
            processor,
            model
        )
        print("Transcript:", transcript)
        print("REACHED SCORE CALCULATION")

        # Calculate similarity score
        score = calculate_score(
            transcript,
            expected_phrase
        )

        print("Score:", score)

        # Generate feedback only for lower scores
        if score >= 85:

            feedback = (
                "Great job! Your pronunciation was "
                "very close."
            )

        else:
            print("Calling Gemini...")

            feedback = generate_feedback(
                transcript,
                expected_phrase,
                score
            )

            print("Feedback:", feedback)

        

        return {
            "transcript": transcript,
            "expected": expected_phrase,
            "score": score,
            "feedback": feedback
        }

    finally:
        # Delete temporary file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        if processed_path and os.path.exists(processed_path):
            os.remove(processed_path)