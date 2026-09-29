from pathlib import Path
from collections import defaultdict
import statistics

from transcribe_test import load_model, transcribe
from ctc_align_test import forced_align_expected, compute_gop


# --------------------------------------------------
# Configuration
# --------------------------------------------------

AUDIO_DIR = Path("test_audio")


# These are the six Version 1 practice items.
#
# The zoo recordings contain:
# "I'm in the zoo."
#
# The others contain the word itself.
practice_items = {
    "sheep": [
        "Test_sheep1.wav",
        "Test_sheep2.wav",
        "Test_sheep3.wav",
        "Test_sheep4.wav",
        "Test_sheep5.wav",
    ],

    "red": [
        "Test_red1.wav",
        "Test_red2.wav",
        "Test_red3.wav",
        "Test_red4.wav",
        "Test_red5.wav",
    ],

    "lamp": [
        "Test_lamp1.wav",
        "Test_lamp2.wav",
        "Test_lamp3.wav",
        "Test_lamp4.wav",
        "Test_lamp5.wav",
    ],

    "three": [
        "Test_three1.wav",
        "Test_three2.wav",
        "Test_three3.wav",
        "Test_three4.wav",
        "Test_three5.wav",
    ],

    "sun": [
        "Test_sun1.wav",
        "Test_sun2.wav",
        "Test_sun3.wav",
        "Test_sun4.wav",
        "Test_sun5.wav",
    ],

    "zoo": [
        "Test_zoo1.wav",
        "Test_zoo2.wav",
        "Test_zoo3.wav",
        "Test_zoo4.wav",
        "Test_zoo5.wav",
    ],
}


expected_text = {
    "sheep": "sheep",
    "red": "red",
    "lamp": "lamp",
    "three": "three",
    "sun": "sun",
    "zoo": "I'm in the zoo.",
}


# Store raw GOP scores by phoneme.
phoneme_scores = defaultdict(list)


# --------------------------------------------------
# Load model
# --------------------------------------------------

processor, model = load_model()


# --------------------------------------------------
# Process recordings
# --------------------------------------------------

for item_name, filenames in practice_items.items():

    print("\n" + "=" * 60)
    print(f"ITEM: {item_name}")
    print(f"EXPECTED: {expected_text[item_name]}")
    print("=" * 60)

    for filename in filenames:

        audio_path = AUDIO_DIR / filename

        print(f"\n--- {filename} ---")

        # Check file exists.
        if not audio_path.exists():

            print("ERROR: File not found.")
            continue

        # Transcribe and get raw logits.
        phoneme_text, logits, decoded_ids = transcribe(
            str(audio_path),
            processor,
            model
        )

        print("Model decoded:", phoneme_text)

        # Convert expected text into the model's phoneme tokens.
        expected_ids = processor.tokenizer(
            expected_text[item_name]
        )["input_ids"]

        expected_phonemes = (
            processor.tokenizer.convert_ids_to_tokens(
                expected_ids
            )
        )

        print(
            "Expected phonemes:",
            " ".join(expected_phonemes)
        )

        # Forced alignment.
        alignment = forced_align_expected(
            logits,
            expected_ids,
            processor.tokenizer.pad_token_id
        )

        # Raw GOP.
        gop_results = compute_gop(
            logits,
            alignment,
            expected_phonemes,
            processor
        )

        # Print and store scores.
        for result in gop_results:

            phoneme = result["phoneme"]
            gop_score = result["gop_score"]

            print(
                f"{phoneme}: "
                f"{gop_score:.2f}"
            )

            phoneme_scores[phoneme].append(
                gop_score
            )


# --------------------------------------------------
# Baseline statistics
# --------------------------------------------------

print("\n" + "=" * 60)
print("BASELINE STATISTICS")
print("=" * 60)

for phoneme in sorted(phoneme_scores):

    scores = phoneme_scores[phoneme]

    mean = statistics.mean(scores)

    if len(scores) >= 2:
        std = statistics.stdev(scores)
    else:
        std = 0.0

    print(
        f"{phoneme}: "
        f"mean={mean:.2f}, "
        f"std={std:.2f}, "
        f"count={len(scores)}"
    )