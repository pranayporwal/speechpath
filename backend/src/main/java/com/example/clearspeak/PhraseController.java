package com.example.clearspeak;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

@RestController
@RequestMapping("/phrases")
public class PhraseController {

    private final PhraseDatabaseService phraseDatabaseService;
    private final ProgressionService progressionService;

    public PhraseController(
            PhraseDatabaseService phraseDatabaseService,
            ProgressionService progressionService
    ) {
        this.phraseDatabaseService = phraseDatabaseService;
        this.progressionService = progressionService;
    }

    @GetMapping("/next")
    public ResponseEntity<PhraseResponse> getNextPhrase(
            @RequestParam String phoneme,
            @RequestParam int level,
            @RequestParam int subLevel,
            @RequestParam(required = false) Integer excludeIndex,
            @RequestParam(required = false) Double score
    ) {

        if (level < 1 || level > 5) {
            return ResponseEntity.badRequest().build();
        }

        if (subLevel < 1 || subLevel > 10) {
            return ResponseEntity.badRequest().build();
        }

        PhraseDatabase database;

        try {
            database = phraseDatabaseService.getDatabase(phoneme);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        }

        // By default, stay at the current level/sub-level.
        int targetLevel = level;
        int targetSubLevel = subLevel;

        // If a score is provided, calculate the next learning position.
        if (score != null) {

            ProgressionService.ProgressionResult progression =
                    progressionService.calculateProgression(
                            level,
                            subLevel,
                            score
                    );

            targetLevel = progression.level();
            targetSubLevel = progression.subLevel();
        }

        PhraseDatabase.Level selectedLevel =
                database.levels().get(targetLevel - 1);

        PhraseDatabase.SubLevel selectedSubLevel =
                selectedLevel.subLevels().get(targetSubLevel - 1);

        List<String> phrases = selectedSubLevel.phrases();

        int selectedIndex = chooseRandomIndex(
                phrases.size(),
                excludeIndex
        );

        String phrase = phrases.get(selectedIndex);

        PhraseResponse response =
                new PhraseResponse(
                        targetLevel,
                        targetSubLevel,
                        selectedIndex,
                        phrase
                );

        return ResponseEntity.ok(response);
    }

    private int chooseRandomIndex(
            int phraseCount,
            Integer excludeIndex
    ) {

        if (phraseCount <= 0) {
            throw new IllegalStateException(
                    "No phrases available."
            );
        }

        if (phraseCount == 1) {
            return 0;
        }

        int index;

        do {
            index = ThreadLocalRandom.current()
                    .nextInt(phraseCount);

        } while (
                excludeIndex != null
                        && index == excludeIndex
        );

        return index;
    }
}