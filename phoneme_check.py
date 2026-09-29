from phonemizer.backend import EspeakBackend


backend = EspeakBackend(
    language="en-us",
    punctuation_marks=None,
    preserve_punctuation=False,
    with_stress=False
)

result = backend.phonemize(
    ["ship"]
)

print("eSpeak phonemizer output:")
print(result)