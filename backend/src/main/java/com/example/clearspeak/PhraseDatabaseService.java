package com.example.clearspeak;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.Map;

@Service
public class PhraseDatabaseService {

    private static final Map<String, String> PHRASE_FILES = Map.of(
            "sh", "phrases/clearspeak_sh_phrase_database.json"
    );

    private final Map<String, PhraseDatabase> databases;

    public PhraseDatabaseService(ObjectMapper objectMapper) {

        this.databases =
                PHRASE_FILES.entrySet()
                        .stream()
                        .collect(
                                java.util.stream.Collectors.toUnmodifiableMap(
                                        Map.Entry::getKey,
                                        entry -> loadDatabase(
                                                objectMapper,
                                                entry.getKey(),
                                                entry.getValue()
                                        )
                                )
                        );

        System.out.println(
                "Phrase databases loaded: "
                        + databases.keySet()
        );
    }

    public PhraseDatabase getDatabase(
            String phoneme
    ) {

        String normalizedPhoneme =
                normalizePhoneme(phoneme);

        PhraseDatabase database =
                databases.get(normalizedPhoneme);

        if (database == null) {

            throw new IllegalArgumentException(
                    "Unsupported phoneme: "
                            + phoneme
            );
        }

        return database;
    }

    private PhraseDatabase loadDatabase(
            ObjectMapper objectMapper,
            String phoneme,
            String filePath
    ) {

        try {

            ClassPathResource resource =
                    new ClassPathResource(filePath);

            if (!resource.exists()) {

                throw new IllegalStateException(
                        "Phrase database not found for phoneme: "
                                + phoneme
                                + " at "
                                + filePath
                );
            }

            PhraseDatabase database =
                    objectMapper.readValue(
                            resource.getInputStream(),
                            PhraseDatabase.class
                    );

            validateDatabase(
                    database,
                    phoneme
            );

            return database;

        } catch (IOException e) {

            throw new IllegalStateException(
                    "Failed to load phrase database for phoneme: "
                            + phoneme,
                    e
            );
        }
    }

    private void validateDatabase(
            PhraseDatabase database,
            String phoneme
    ) {

        if (database == null
                || database.levels() == null
                || database.levels().size() != 5) {

            throw new IllegalStateException(
                    "Database for "
                            + phoneme
                            + " must contain exactly 5 levels."
            );
        }

        for (PhraseDatabase.Level level
                : database.levels()) {

            if (level.subLevels() == null
                    || level.subLevels().size() != 10) {

                throw new IllegalStateException(
                        "Level "
                                + level.level()
                                + " in database "
                                + phoneme
                                + " must contain exactly 10 sub-levels."
                );
            }

            for (PhraseDatabase.SubLevel subLevel
                    : level.subLevels()) {

                if (subLevel.phrases() == null
                        || subLevel.phrases().size() != 6) {

                    throw new IllegalStateException(
                            "Level "
                                    + level.level()
                                    + ", sub-level "
                                    + subLevel.subLevel()
                                    + " in database "
                                    + phoneme
                                    + " must contain exactly 6 phrases."
                    );
                }
            }
        }
    }

    private String normalizePhoneme(String phoneme) {
        if (phoneme == null || phoneme.isBlank()) {
            throw new IllegalArgumentException(
                    "Phoneme must not be empty."
            );
        }

        return phoneme
                .trim()
                .toLowerCase()
                .replace("/", "");
    }
}