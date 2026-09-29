import sys
import torch
import librosa

from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor


# Phoneme-recognition model using eSpeak phoneme labels.
MODEL_NAME = "facebook/wav2vec2-lv-60-espeak-cv-ft"


def load_model():
    print("Loading Wav2Vec2 phoneme model...")

    processor = Wav2Vec2Processor.from_pretrained(
        MODEL_NAME
    )

    model = Wav2Vec2ForCTC.from_pretrained(
        MODEL_NAME
    )

    model.eval()

    print("Model loaded!")

    return processor, model


def collapse_ctc_ids(token_ids, blank_id):
    """
    Collapse a greedy CTC path:
    - remove repeated consecutive tokens
    - remove blank tokens

    Example:
        [0, 38, 38, 0, 17, 17, 18]
        -> [38, 17, 18]
    """

    collapsed = []
    previous = None

    for token_id in token_ids:

        if token_id == blank_id:
            previous = token_id
            continue

        if token_id != previous:
            collapsed.append(token_id)

        previous = token_id

    return collapsed


def token_ids_to_phonemes(
    token_ids,
    processor
):
    """Convert model token IDs into readable phoneme symbols."""

    return processor.tokenizer.convert_ids_to_tokens(
        token_ids
    )


def transcribe(
    audio_path,
    processor,
    model
):
    print("Loading audio...")

    audio, sample_rate = librosa.load(
        audio_path,
        sr=16000,
        mono=True
    )

    print("Audio samples:", len(audio))
    print("Max amplitude:", max(abs(audio)))
    print(
        "Audio duration:",
        len(audio) / 16000,
        "seconds"
    )

    inputs = processor(
        audio,
        sampling_rate=16000,
        return_tensors="pt"
    )

    with torch.no_grad():
        logits = model(
            inputs.input_values
        ).logits

    # Greedy CTC decoding.
    predicted_ids = torch.argmax(
        logits,
        dim=-1
    )[0].tolist()

    blank_id = processor.tokenizer.pad_token_id

    # Collapse the CTC path into phoneme tokens.
    decoded_ids = collapse_ctc_ids(
        predicted_ids,
        blank_id
    )

    phonemes = token_ids_to_phonemes(
        decoded_ids,
        processor
    )

    phoneme_text = " ".join(
        phonemes
    )

    return (
        phoneme_text,
        logits,
        decoded_ids
    )


# --------------------------------------------------
# Standalone test
# --------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(
            "Usage: python transcribe_test.py path/to/audio.wav"
        )
        sys.exit(1)

    audio_path = sys.argv[1]

    processor, model = load_model()

    phonemes, logits, decoded_ids = transcribe(
        audio_path,
        processor,
        model
    )

    print("\nPhonemes:")
    print(phonemes)

    print("\nDecoded IDs:")
    print(decoded_ids)

    print("\nLogits shape:")
    print(logits.shape)