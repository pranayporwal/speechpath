import sys
import torch
import librosa

from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor


MODEL_NAME = "facebook/wav2vec2-base-960h"


def load_model():
    print("Loading Wav2Vec2 model...")

    processor = Wav2Vec2Processor.from_pretrained(MODEL_NAME)
    model = Wav2Vec2ForCTC.from_pretrained(MODEL_NAME)

    model.eval()

    print("Model loaded!")

    return processor, model


def transcribe(audio_path, processor, model):
    print("Loading audio...")

    audio, sample_rate = librosa.load(
        audio_path,
        sr=16000,
        mono=True
    )
    print("Audio samples:", len(audio))
    print("Max amplitude:", max(abs(audio)))
    print("Audio duration:", len(audio) / 16000, "seconds")

    inputs = processor(
        audio,
        sampling_rate=16000,
        return_tensors="pt"
    )

    with torch.no_grad():
        logits = model(inputs.input_values).logits

    predicted_ids = torch.argmax(logits, dim=-1)

    transcription = processor.batch_decode(
        predicted_ids
    )[0]

    return transcription


# This part only runs when you directly execute:
# python transcribe_test.py Test.wav
if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python transcribe_test.py path/to/audio.wav")
        sys.exit(1)

    audio_path = sys.argv[1]

    processor, model = load_model()

    text = transcribe(
        audio_path,
        processor,
        model
    )

    print("\nTranscript:")
    print(text)