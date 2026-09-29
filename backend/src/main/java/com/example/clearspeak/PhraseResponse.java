package com.example.clearspeak;

public record PhraseResponse(
        int level,
        int subLevel,
        int index,
        String phrase
) {
}
