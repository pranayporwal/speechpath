from pathlib import Path

from transcribe_test import load_model, transcribe
from ctc_align_test import forced_align_expected, compute_gop
from pronunciation_scorer_v1 import calculate_score


AUDIO_DIR = Path("test_audio")
processor, model = load_model()


TESTS = {
    "sheep": "sheep",
    "red": "red",
    "lamp": "lamp",
    "three": "three",
    "sun": "sun",
    "zoo": "I'm in the zoo.",
}


for item, expected_text in TESTS.items():

    print("\n" + "=" * 60)
    print(f"ITEM: {item}")
    print(f"EXPECTED: {expected_text}")
    print("=" * 60)

    scores = []

    for count in range(1, 6):

        filename = f"Test_{item}{count}.wav"

        audio_path = AUDIO_DIR / filename

        if not audio_path.exists():
            print("FILE NOT FOUND:", audio_path)
            continue

        print("\n" + "-" * 50)
        print(f"FILE: {filename}")
        print("-" * 50)

        phoneme_text, logits, decoded_ids = transcribe(
            str(audio_path),
            processor,
            model
        )

        print("Model decoded:", phoneme_text)

        expected_ids = processor.tokenizer(
            expected_text
        )["input_ids"]

        expected_phonemes = (
            processor.tokenizer.convert_ids_to_tokens(
                expected_ids
            )
        )

        alignment = forced_align_expected(
            logits,
            expected_ids,
            processor.tokenizer.pad_token_id
        )

        gop_results = compute_gop(
            logits,
            alignment,
            expected_phonemes,
            processor
        )

        score_input = []

        for result in gop_results:
            score_input.append({
                "phoneme": result["phoneme"],
                "gop_score": result["gop_score"]
            })

        score, breakdown = calculate_score(
            score_input
        )

        scores.append(score)

        print("PHONEME SCORES:")

        for item_result in breakdown:
            print(
                f"{item_result['phoneme']}: "
                f"raw={item_result['raw_gop']:.2f} | "
                f"calibrated={item_result['calibrated_score']:.2f}"
            )

        print(f"FINAL SCORE: {score:.2f}")

    if scores:

        average_score = sum(scores) / len(scores)

        print("\n" + "=" * 60)
        print(f"{item.upper()} SCORE SUMMARY")
        print("=" * 60)

        print(
            "Scores:",
            ", ".join(
                f"{score:.2f}"
                for score in scores
            )
        )

        print(
            f"Average: {average_score:.2f}"
        )