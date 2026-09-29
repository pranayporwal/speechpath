import os
import tempfile

import librosa
import soundfile as sf
import torch
import google.generativeai as genai

from Levenshtein import editops
from pronunciation_scorer_v1 import calculate_score

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from transcribe_test import (
    load_model,
    transcribe
)


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI()


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Load Wav2Vec2 ONCE
# --------------------------------------------------

processor, model = load_model()


# --------------------------------------------------
# Configure Gemini
# --------------------------------------------------

gemini_api_key = os.environ.get(
    "GEMINI_API_KEY"
)

if gemini_api_key:

    genai.configure(
        api_key=gemini_api_key
    )

    gemini_model = genai.GenerativeModel(
        "gemini-3.6-flash"
    )

else:

    gemini_model = None


# --------------------------------------------------
# Audio preprocessing
# --------------------------------------------------

def preprocess_audio(input_path):

    audio, sample_rate = librosa.load(
        input_path,
        sr=16000,
        mono=True
    )

    # Normalize volume.
    max_amplitude = max(abs(audio))

    if max_amplitude > 0:
        audio = audio / max_amplitude

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


# --------------------------------------------------
# CTC forced alignment
# --------------------------------------------------

def forced_align_expected(
    logits,
    expected_phoneme_ids,
    blank_id
):
    """
    Align the expected phoneme sequence to the
    model's frame-level CTC probabilities.

    CTC needs blank states between target phonemes:

        [blank, p1, blank, p2, blank, p3, blank]

    We use dynamic programming to find the
    highest-probability path through those states.

    Returns:
        List of dictionaries containing:
        - phoneme token ID
        - start frame
        - end frame
    """

    log_probs = torch.log_softmax(
        logits[0],
        dim=-1
    )

    num_frames = log_probs.shape[0]

    # Example:
    # expected = [SH, IH, P]
    #
    # expanded =
    # [blank, SH, blank, IH, blank, P, blank]
    expanded = []

    for phoneme_id in expected_phoneme_ids:

        expanded.append(blank_id)
        expanded.append(phoneme_id)

    expanded.append(blank_id)

    num_states = len(expanded)

    # dp[t][s] = best log probability of reaching
    # state s at frame t.
    dp = torch.full(
        (num_frames, num_states),
        float("-inf")
    )

    # Store the previous state so we can backtrack.
    backpointer = torch.full(
        (num_frames, num_states),
        -1,
        dtype=torch.long
    )

    # First frame.
    dp[0, 0] = log_probs[
        0,
        blank_id
    ]

    if num_states > 1:

        dp[0, 1] = log_probs[
            0,
            expanded[1]
        ]

    for t in range(1, num_frames):

        for s in range(num_states):

            current_token = expanded[s]

            best_previous_state = s
            best_score = dp[
                t - 1,
                s
            ]

            # Move from the previous state.
            if s > 0:

                candidate = dp[
                    t - 1,
                    s - 1
                ]

                if candidate > best_score:

                    best_score = candidate
                    best_previous_state = s - 1

            # Skip the blank / previous token state.
            #
            # This is only legal for a real phoneme,
            # and only when it isn't the same phoneme
            # as the state two positions earlier.
            if (
                s > 1
                and current_token != blank_id
                and current_token != expanded[s - 2]
            ):

                candidate = dp[
                    t - 1,
                    s - 2
                ]

                if candidate > best_score:

                    best_score = candidate
                    best_previous_state = s - 2

            dp[t, s] = (
                best_score
                + log_probs[t, current_token]
            )

            backpointer[
                t,
                s
            ] = best_previous_state

    # CTC can finish in either the final blank
    # or the final phoneme state.
    final_states = [
        num_states - 1,
        num_states - 2
    ]

    final_state = max(
        final_states,
        key=lambda s: dp[
            num_frames - 1,
            s
        ].item()
    )

    # Backtrack the best path.
    states = []

    state = final_state

    for t in range(
        num_frames - 1,
        -1,
        -1
    ):

        states.append(state)

        if t > 0:

            state = int(
                backpointer[
                    t,
                    state
                ]
            )

    states.reverse()

    # Collect frame ranges for every expected phoneme.
    alignment = []

    for phoneme_index, phoneme_id in enumerate(
        expected_phoneme_ids
    ):

        state_index = 2 * phoneme_index + 1

        frames = [
            frame_index
            for frame_index, state in enumerate(states)
            if state == state_index
        ]

        if not frames:

            alignment.append({
                "phoneme_id": phoneme_id,
                "start_frame": None,
                "end_frame": None
            })

        else:

            alignment.append({
                "phoneme_id": phoneme_id,
                "start_frame": min(frames),
                "end_frame": max(frames)
            })

    return alignment


# --------------------------------------------------
# GOP confidence
# --------------------------------------------------

def compute_gop(
    logits,
    alignment,
    expected_phoneme_ids
):
    """
    Calculate a practical GOP-style confidence score
    for every expected phoneme.

    We use the highest-probability aligned CTC frame
    (the phoneme spike) rather than averaging across
    blank-heavy frames.
    """

    log_probs = torch.log_softmax(
        logits[0],
        dim=-1
    )

    blank_id = 0

    breakdown = []

    for index, phoneme_id in enumerate(
        expected_phoneme_ids
    ):

        item = alignment[index]

        start = item["start_frame"]
        end = item["end_frame"]

        # If the phoneme could not be aligned,
        # assign zero confidence.
        if (
            start is None
            or end is None
            or end < start
        ):
            breakdown.append({
                "phoneme_id": phoneme_id,
                "gop_score": 0.0,
                "start_frame": start,
                "end_frame": end
            })

            continue

        # Our forced alignment often assigns a phoneme
        # to one spike frame. Use that frame.
        frame = start

        target_probability = torch.exp(
            log_probs[
                frame,
                phoneme_id
            ]
        ).item()

        # Remove blank from competitor search.
        frame_log_probs = log_probs[
            frame
        ].clone()

        frame_log_probs[
            blank_id
        ] = float("-inf")

        values, ids = torch.topk(
            frame_log_probs,
            k=5
        )

        competitor_probability = 0.0

        for value, token_id in zip(
            values.tolist(),
            ids.tolist()
        ):

            if token_id != phoneme_id:

                competitor_probability = (
                    torch.exp(
                        torch.tensor(value)
                    ).item()
                )

                break

        denominator = (
            target_probability
            + competitor_probability
        )

        if denominator > 0:

            relative_confidence = (
                target_probability
                / denominator
            )

        else:

            relative_confidence = 0.0

        gop_score = (
            relative_confidence * 100
        )

        breakdown.append({
            "phoneme_id": phoneme_id,
            "gop_score": round(
                max(
                    0.0,
                    min(
                        100.0,
                        gop_score
                    )
                ),
                1
            ),
            "start_frame": start,
            "end_frame": end
        })

    return breakdown


# --------------------------------------------------
# Levenshtein edit errors
# --------------------------------------------------

def detect_edit_errors(
    expected_phonemes,
    decoded_phonemes
):
    """
    Compare expected and greedy-decoded phoneme
    tokens and report substitutions, deletions
    and insertions.

    We encode each phoneme token as a unique private
    Unicode character so python-Levenshtein can work
    on token sequences without treating characters
    inside multi-character phoneme tokens separately.

    Example:

        expected = [ʃ, ɪ, p]
        actual   = [ʃ, ɪ, b]

        -> substitution p -> b
    """

    all_tokens = list(
        dict.fromkeys(
            expected_phonemes
            + decoded_phonemes
        )
    )

    token_to_char = {
        token: chr(
            0xE000 + index
        )
        for index, token in enumerate(
            all_tokens
        )
    }

    expected_string = "".join(
        token_to_char[token]
        for token in expected_phonemes
    )

    decoded_string = "".join(
        token_to_char[token]
        for token in decoded_phonemes
    )

    operations = editops(
        expected_string,
        decoded_string
    )

    errors = []

    for operation, source_index, dest_index in operations:

        if operation == "replace":

            errors.append({
                "type": "substitution",
                "expected": expected_phonemes[
                    source_index
                ],
                "actual": decoded_phonemes[
                    dest_index
                ]
            })

        elif operation == "delete":

            errors.append({
                "type": "deletion",
                "expected": expected_phonemes[
                    source_index
                ]
            })

        elif operation == "insert":

            errors.append({
                "type": "insertion",
                "actual": decoded_phonemes[
                    dest_index
                ]
            })

    return errors


# --------------------------------------------------
# Combine GOP + edit errors
# --------------------------------------------------

def combine_score(
    gop_scores,
    edit_errors,
    expected_phonemes
):
    """
    Combine:
    1. average GOP confidence
    2. edit-distance error penalties

    Penalties:
        substitution = -8
        insertion    = -5
        deletion     = -5

    The result is clipped to [0, 100].
    """

    if not gop_scores:

        return 0, []

    base_score = sum(
        item["gop_score"]
        for item in gop_scores
    ) / len(gop_scores)

    score = base_score

    for error in edit_errors:

        if error["type"] == "substitution":

            score -= 8

        elif error["type"] == "insertion":

            score -= 5

        elif error["type"] == "deletion":

            score -= 5

    score = max(
        0,
        min(
            100,
            round(score)
        )
    )

    # Attach error information to each expected
    # phoneme so the Android UI / Gemini can inspect it.
    breakdown = []

    for item, phoneme in zip(
        gop_scores,
        expected_phonemes
    ):

        matching_errors = []

        for error in edit_errors:

            if (
                error.get("expected")
                == phoneme
            ):

                matching_errors.append(
                    error
                )

        breakdown.append({
            "phoneme": phoneme,
            "gop_score": item[
                "gop_score"
            ],
            "errors": matching_errors,
            "start_frame": item[
                "start_frame"
            ],
            "end_frame": item[
                "end_frame"
            ]
        })

    # Insertions do not correspond to an expected
    # phoneme, so add them separately.
    for error in edit_errors:

        if error["type"] == "insertion":

            breakdown.append({
                "phoneme": None,
                "gop_score": None,
                "errors": [error],
                "start_frame": None,
                "end_frame": None
            })

    return score, breakdown


# --------------------------------------------------
# Gemini feedback
# --------------------------------------------------

def generate_feedback(
    transcript,
    expected_phrase,
    score,
    phoneme_breakdown
):

    if gemini_model is None:

        return "Keep practicing that phrase!"

    low_confidence = [
        item
        for item in phoneme_breakdown
        if (
            item["gop_score"] is not None
            and item["gop_score"] < 70
        )
        or item["errors"]
    ]

    prompt = f"""
The user was asked to say:
"{expected_phrase}"

The model transcribed their speech as:
"{transcript}"

Their overall pronunciation score is:
{score}/100.

Phoneme-level analysis:
{low_confidence}

Give one short encouraging corrective tip
focused on the lowest-confidence or clearly
incorrect sound.

Mention the specific sound when useful.
Be supportive and simple.
Do not diagnose anything.
"""

    try:

        print(
            "Sending request to Gemini..."
        )

        response = gemini_model.generate_content(
            prompt
        )

        print(
            "Gemini response received."
        )

        if response.text:

            return response.text.strip()

        return "Keep practicing that phrase!"

    except Exception as e:

        print(
            "Gemini feedback error:",
            e
        )

        return "Keep practicing that phrase!"


# --------------------------------------------------
# POST /assess
# --------------------------------------------------

@app.post("/assess")
async def assess(
    audio: UploadFile = File(...),
    expected_phrase: str = Form(...)
):

    print(
        "Received audio:",
        audio.filename
    )

    print(
        "Expected phrase:",
        expected_phrase
    )

    temp_path = None
    processed_path = None

    try:

        # ------------------------------------------
        # Save uploaded audio
        # ------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        ) as temp_file:

            temp_path = temp_file.name

            content = await audio.read()

            print(
                "Received file size:",
                len(content),
                "bytes"
            )

            temp_file.write(content)


        # ------------------------------------------
        # Preprocess audio
        # ------------------------------------------

        processed_path = preprocess_audio(
            temp_path
        )


        # ------------------------------------------
        # Wav2Vec2 phoneme recognition
        # ------------------------------------------

        (
            phoneme_text,
            logits,
            decoded_ids
        ) = transcribe(
            processed_path,
            processor,
            model
        )

        print(
            "Greedy phonemes:",
            phoneme_text
        )


        # ------------------------------------------
        # Expected phoneme sequence
        #
        # IMPORTANT:
        # Use the SAME tokenizer as the phoneme model.
        # This avoids the ARPAbet -> IPA mapping problem.
        # ------------------------------------------

        expected_encoding = (
            processor.tokenizer(
                expected_phrase
            )
        )

        expected_phoneme_ids = (
            expected_encoding[
                "input_ids"
            ]
        )

        expected_phonemes = (
            processor.tokenizer.convert_ids_to_tokens(
                expected_phoneme_ids
            )
        )

        print(
            "Expected phonemes:",
            " ".join(expected_phonemes)
        )


        # ------------------------------------------
        # Forced alignment
        # ------------------------------------------

        blank_id = (
            processor.tokenizer.pad_token_id
        )

        alignment = forced_align_expected(
            logits,
            expected_phoneme_ids,
            blank_id
        )


        # ------------------------------------------
        # GOP scoring
        # ------------------------------------------

        gop_scores = compute_gop(
            logits,
            alignment,
            expected_phoneme_ids
        )


        # ------------------------------------------
        # Greedy decoded phoneme errors
        # ------------------------------------------

        decoded_phonemes = (
            processor.tokenizer.convert_ids_to_tokens(
                decoded_ids
            )
        )

        edit_errors = detect_edit_errors(
            expected_phonemes,
            decoded_phonemes
        )


        # ------------------------------------------
        # Final pronunciation score
        # ------------------------------------------

        # ------------------------------------------
        # Calibrated pronunciation score
        # ------------------------------------------

        gop_results_for_scorer = []

        for item, phoneme in zip(
            gop_scores,
            expected_phonemes
        ):
            gop_results_for_scorer.append({
                **item,
                "phoneme": phoneme
            })

        score, calibrated_breakdown = calculate_score(
            gop_results_for_scorer
        )

        # Attach edit-error information so Gemini
        # and Android can still use it.
        phoneme_breakdown = []

        for item in calibrated_breakdown:

            phoneme = item["phoneme"]

            matching_errors = []

            for error in edit_errors:

                if error.get("expected") == phoneme:
                    matching_errors.append(error)

            phoneme_breakdown.append({
                "phoneme": phoneme,
                "gop_score": item["raw_gop"],
                "calibrated_score": item["calibrated_score"],
                "weight": item["weight"],
                "errors": matching_errors
            })

        print(
            "Pronunciation score:",
            score
        )

        print(
            "Phoneme errors:",
            edit_errors
        )


        # ------------------------------------------
        # Gemini feedback
        # ------------------------------------------

        if score >= 85:

            feedback = (
                "Great job! Your pronunciation "
                "was very close."
            )

        else:

            feedback = generate_feedback(
                phoneme_text,
                expected_phrase,
                score,
                phoneme_breakdown
            )

        print(
            "Feedback:",
            feedback
        )


        # ------------------------------------------
        # Return result
        # ------------------------------------------

        return {
            "transcript": phoneme_text,
            "expected": expected_phrase,
            "score": score,
            "phoneme_errors": edit_errors,
            "phoneme_breakdown": phoneme_breakdown,
            "feedback": feedback
        }


    finally:

        # Delete temporary files.
        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            os.remove(temp_path)

        if (
            processed_path
            and os.path.exists(processed_path)
        ):

            os.remove(processed_path)