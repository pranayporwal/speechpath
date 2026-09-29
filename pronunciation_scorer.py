# Experimental baseline means.
# We will replace these with the final clean baseline
# for sheep, red, lamp, three, sun, and zoo later.

BASELINE_MEANS = {
    "ʃ": 98.05,
    "ɪ": 56.40,
    "iː": 84.33,
    "p": 94.75,
    "k": 70.88,
    "æ": 5.17,
    "b": 98.23,
    "ɹ": 32.33,
    "ɛ": 73.17,
    "d": 85.43,
}


# Experimental reliability weights.
# These are temporary and will be refined later.
PHONEME_WEIGHTS = {
    "ʃ": 1.0,
    "ɪ": 0.9,
    "iː": 0.9,
    "p": 1.0,
    "k": 0.5,
    "æ": 0.7,
    "b": 1.0,
    "ɹ": 0.5,
    "ɛ": 0.8,
    "d": 0.7,
}


def calculate_calibrated_score(
    raw_gop,
    phoneme
):
    """
    Convert raw GOP into a phoneme-specific
    calibrated score from 0 to 100.
    """

    baseline = BASELINE_MEANS.get(phoneme)

    if baseline is None:
        return raw_gop

    if baseline <= 0:
        return 0.0

    calibrated_score = (
        raw_gop / baseline
    ) * 100

    return min(
        100.0,
        max(
            0.0,
            calibrated_score
        )
    )


def calculate_word_score(
    gop_results
):
    """
    Calculate a reliability-weighted
    pronunciation score for the word.
    """

    weighted_sum = 0.0
    total_weight = 0.0

    breakdown = []

    for result in gop_results:

        phoneme = result["phoneme"]
        raw_gop = result["gop_score"]

        calibrated_score = calculate_calibrated_score(
            raw_gop,
            phoneme
        )

        weight = PHONEME_WEIGHTS.get(
            phoneme,
            0.5
        )

        weighted_sum += (
            calibrated_score * weight
        )

        total_weight += weight

        breakdown.append({
            "phoneme": phoneme,
            "raw_gop": raw_gop,
            "calibrated_score": round(
                calibrated_score,
                2
            ),
            "weight": weight
        })

    if total_weight == 0:
        word_score = 0.0
    else:
        word_score = (
            weighted_sum / total_weight
        )

    return round(
        word_score,
        2
    ), breakdown