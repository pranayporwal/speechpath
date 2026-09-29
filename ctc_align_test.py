import torch

def forced_align_expected(
    logits,
    expected_phoneme_ids,
    blank_id
):
    """
    CTC Viterbi forced alignment.

    Finds the highest-probability CTC path that produces
    the expected phoneme sequence.

    Returns the frame range assigned to each phoneme.
    """

    # Convert raw logits to log-probabilities.
    log_probs = torch.log_softmax(
        logits[0],
        dim=-1
    )

    num_frames = log_probs.shape[0]

    # Expand target for CTC:
    #
    # h ə l
    #
    # becomes:
    #
    # blank h blank ə blank l blank
    #
    expanded = [blank_id]

    for phoneme_id in expected_phoneme_ids:
        expanded.append(phoneme_id)
        expanded.append(blank_id)

    num_states = len(expanded)

    # Dynamic-programming table.
    dp = torch.full(
        (num_frames, num_states),
        float("-inf")
    )

    # Store previous state for backtracking.
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

    # Fill DP table.
    for t in range(1, num_frames):

        for s in range(num_states):

            current_token = expanded[s]

            # Option 1: remain in the same state.
            best_score = dp[
                t - 1,
                s
            ]

            best_state = s

            # Option 2: move from previous state.
            if s > 0:

                candidate = dp[
                    t - 1,
                    s - 1
                ]

                if candidate > best_score:

                    best_score = candidate
                    best_state = s - 1

            # Option 3: skip over a blank and
            # previous phoneme.
            #
            # This is only allowed for a real phoneme,
            # and not when it repeats the previous phoneme.
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
                    best_state = s - 2

            dp[t, s] = (
                best_score
                + log_probs[
                    t,
                    current_token
                ]
            )

            backpointer[
                t,
                s
            ] = best_state

    # CTC can finish either on the final phoneme
    # or on the final blank.
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
    state_path = []

    state = final_state

    for t in range(
        num_frames - 1,
        -1,
        -1
    ):

        state_path.append(state)

        if t > 0:
            state = int(
                backpointer[
                    t,
                    state
                ]
            )

    state_path.reverse()

    # Convert state positions into phoneme frame ranges.
    alignment = []

    for index, phoneme_id in enumerate(
        expected_phoneme_ids
    ):

        state_index = (
            2 * index + 1
        )

        frames = [
            frame
            for frame, state in enumerate(
                state_path
            )
            if state == state_index
        ]

        if frames:

            alignment.append({
                "phoneme_id": phoneme_id,
                "start_frame": min(frames),
                "end_frame": max(frames)
            })

        else:

            alignment.append({
                "phoneme_id": phoneme_id,
                "start_frame": None,
                "end_frame": None
            })

    return alignment

# --------------------------------------------------
# GOP diagnostic
# --------------------------------------------------

def compute_gop(
    logits,
    alignment,
    expected_phonemes,
    processor
):
    """
    Calculate a GOP-style pronunciation confidence
    for each expected phoneme.

    For each aligned phoneme:

        confidence =
            P(expected)
            --------------------------
            P(expected) + P(best competitor)

    This gives a relative confidence score between
    0 and 1, which we convert to 0-100.

    This is a practical GOP-style score, not a
    clinically validated pronunciation measure.
    """

    log_probs = torch.log_softmax(
        logits[0],
        dim=-1
    )

    blank_id = processor.tokenizer.pad_token_id

    results = []

    for phoneme, item in zip(
        expected_phonemes,
        alignment
    ):

        frame = item["start_frame"]

        # If the phoneme could not be aligned,
        # assign zero confidence.
        if frame is None:

            results.append({
                "phoneme": phoneme,
                "gop_score": 0.0,
                "target_probability": 0.0,
                "competitor": None,
                "competitor_probability": 0.0
            })

            continue

        phoneme_id = (
            processor.tokenizer
            .convert_tokens_to_ids(
                phoneme
            )
        )

        # Probability of the expected phoneme
        # at the aligned CTC frame.
        target_probability = torch.exp(
            log_probs[
                frame,
                phoneme_id
            ]
        ).item()

        # Ignore the CTC blank when looking for
        # the strongest competing phoneme.
        frame_log_probs = (
            log_probs[frame].clone()
        )

        frame_log_probs[
            blank_id
        ] = float("-inf")

        values, ids = torch.topk(
            frame_log_probs,
            k=5
        )

        competitor = None
        competitor_probability = 0.0

        for value, token_id in zip(
            values.tolist(),
            ids.tolist()
        ):

            token = (
                processor.tokenizer
                .convert_ids_to_tokens(
                    token_id
                )
            )

            # Don't use the expected phoneme itself
            # as its own competitor.
            if token != phoneme:

                competitor = token

                competitor_probability = (
                    torch.exp(
                        torch.tensor(value)
                    ).item()
                )

                break

        # Relative confidence:
        #
        # 1.0  -> target strongly wins
        # 0.5  -> target and competitor are equal
        # 0.0  -> competitor strongly wins
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

        results.append({
            "phoneme": phoneme,
            "gop_score": round(
                gop_score,
                1
            ),
            "target_probability": round(
                target_probability,
                4
            ),
            "competitor": competitor,
            "competitor_probability": round(
                competitor_probability,
                4
            ),
            "frame": frame
        })

    return results