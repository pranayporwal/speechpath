package com.example.clearspeak;

import org.springframework.stereotype.Service;

@Service
public class ProgressionService {

    public ProgressionResult calculateProgression(
            int currentLevel,
            int currentSubLevel,
            double score
    ) {

        int level = currentLevel;
        int subLevel = currentSubLevel;

        if (score >= 80) {

            if (subLevel < 10) {
                subLevel++;
            } else if (level < 5) {
                level++;
                subLevel = 1;
            }

        } else if (score < 50) {

            if (subLevel > 1) {
                subLevel--;
            } else if (level > 1) {
                level--;
                subLevel = 10;
            }
        }

        return new ProgressionResult(level, subLevel);
    }

    public record ProgressionResult(
            int level,
            int subLevel
    ) {}
}
