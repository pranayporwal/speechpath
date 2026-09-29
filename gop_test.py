import torch

from transcribe_test import load_model, transcribe


processor, model = load_model()

# Your Test.wav
phonemes, logits, decoded_ids = transcribe(
    "Test.wav",
    processor,
    model
)

# Expected pronunciation of "ship"
expected_ids = processor.tokenizer(
    "hello im pranay porwal"
)["input_ids"]

print("Expected IDs:", expected_ids)

print(
    "Expected phonemes:",
    processor.tokenizer.convert_ids_to_tokens(
        expected_ids
    )
)

print(
    "Decoded phonemes:",
    phonemes
)

print(
    "Logits shape:",
    logits.shape
)

# Show the strongest tokens for every frame.
log_probs = torch.log_softmax(
    logits[0],
    dim=-1
)

top_values, top_ids = torch.topk(
    log_probs,
    k=5,
    dim=-1
)

print("\nFirst 10 frames:")
for frame in range(
    min(10, log_probs.shape[0])
):

    tokens = processor.tokenizer.convert_ids_to_tokens(
        top_ids[frame].tolist()
    )

    print(
        frame,
        list(zip(
            tokens,
            top_values[frame].tolist()
        ))
    )