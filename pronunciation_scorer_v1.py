# Temporary Version 1 scorer
# Uses the baseline from the 30 demo recordings.

BASELINE_MEANS = {
    "aɪ": 11.34,
    "d": 76.82,
    "iː": 65.47,
    "l": 99.54,
    "m": 97.67,
    "n": 98.46,
    "p": 96.94,
    "s": 99.58,
    "uː": 68.58,
    "z": 98.22,
    "æ": 77.40,
    "ð": 0.12,
    "ə": 4.56,
    "ɛ": 68.10,
    "ɪ": 7.64,
    "ɹ": 23.72,
    "ʃ": 98.27,
    "ʌ": 83.02,
    "θ": 0.14,
}


# Simple weights chosen for Version 1.
# We can tune these later based on test results.

PHONEME_WEIGHTS = {
    "aɪ": 1.0,
    "d": 1.0,
    "iː": 1.0,
    "l": 1.0,
    "m": 1.0,
    "n": 1.0,
    "p": 1.0,
    "s": 1.0,
    "uː": 1.0,
    "z": 1.0,
    "æ": 1.0,
    "ð": 1.0,
    "ə": 1.0,
    "ɛ": 1.0,
    "ɪ": 1.0,
    "ɹ": 1.0,
    "ʃ": 1.0,
    "ʌ": 1.0,
    "θ": 1.0,
}


def calculate_calibrated_score(
    raw_gop,
    phoneme
):
    """
    Compare the raw GOP against the observed
    correct-pronunciation baseline for this phoneme.
    """

    baseline = BASELINE_MEANS.get(
        phoneme
    )

    if baseline is None:
        return round(
            max(
                0.0,
                min(
                    100.0,
                    raw_gop
                )
            ),
            2
        )

    if baseline <= 0:
        return 0.0

    calibrated_score = (
        raw_gop / baseline
    ) * 100

    return round(
        max(
            0.0,
            min(
                100.0,
                calibrated_score
            )
        ),
        2
    )


def calculate_score(
    gop_results
):
    """
    Calculate the final score from all phonemes.

    This works for both individual words and
    complete sentences.
    """

    weighted_sum = 0.0
    total_weight = 0.0

    breakdown = []

    for result in gop_results:

        phoneme = result["phoneme"]
        raw_gop = result["gop_score"]

        calibrated_score = (
            calculate_calibrated_score(
                raw_gop,
                phoneme
            )
        )

        weight = PHONEME_WEIGHTS.get(
            phoneme,
            1.0
        )

        weighted_sum += (
            calibrated_score
            * weight
        )

        total_weight += weight

        breakdown.append({
            "phoneme": phoneme,
            "raw_gop": raw_gop,
            "calibrated_score": calibrated_score,
            "weight": weight
        })

    if total_weight == 0:
        return 0.0, breakdown

    final_score = (
        weighted_sum
        / total_weight
    )

    return round(
        final_score,
        2
    ), breakdown