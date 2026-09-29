package com.example.clearspeak;

import java.util.List;

public record PhraseDatabase(
        List<Level> levels
) {

    public record Level(
            int level,
            String name,
            List<SubLevel> subLevels
    ) {
    }

    public record SubLevel(
            int subLevel,
            List<String> phrases
    ) {
    }
}
