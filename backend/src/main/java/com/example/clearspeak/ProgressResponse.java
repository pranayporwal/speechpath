package com.example.clearspeak;

public record ProgressResponse(
        String phoneme,
        int level,
        int subLevel
) {
}
