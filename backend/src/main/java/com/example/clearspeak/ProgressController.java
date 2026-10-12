package com.example.clearspeak;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/progress")
public class ProgressController {

    private final UserPhonemeProgressRepository progressRepository;
    private final UserRepository userRepository;

    private static final List<String> PHONEMES =
            List.of("sh", "r", "l", "th", "s", "z");

    public ProgressController(
            UserPhonemeProgressRepository progressRepository,
            UserRepository userRepository
    ) {
        this.progressRepository = progressRepository;
        this.userRepository = userRepository;
    }

    @GetMapping("/{userId}")
    public ResponseEntity<List<ProgressResponse>> getProgress(
            @PathVariable Long userId
    ) {

        if (!userRepository.existsById(userId)) {
            return ResponseEntity.notFound().build();
        }

        List<UserPhonemeProgress> savedProgress =
                progressRepository.findByUserId(userId);

        List<ProgressResponse> result =
                new ArrayList<>();

        for (String phoneme : PHONEMES) {

            int level = 1;
            int subLevel = 1;

            for (UserPhonemeProgress progress : savedProgress) {

                if (progress.getPhoneme().equals(phoneme)) {

                    level = progress.getLevel();
                    subLevel = progress.getSubLevel();

                    break;
                }
            }

            result.add(
                    new ProgressResponse(
                            phoneme,
                            level,
                            subLevel
                    )
            );
        }

        return ResponseEntity.ok(result);
    }

    @PutMapping("/{userId}/{phoneme}")
    public ProgressResponse updateProgress(
            @PathVariable Long userId,
            @PathVariable String phoneme,
            @RequestParam int score
    ) {

        UserPhonemeProgress progress =
                progressRepository.findById(
                        new UserPhonemeProgressId(userId, phoneme)
                ).orElseGet(() -> {

                    UserPhonemeProgress p = new UserPhonemeProgress();

                    p.setUserId(userId);
                    p.setPhoneme(phoneme);
                    p.setLevel(1);
                    p.setSubLevel(1);

                    return p;
                });

        int level = progress.getLevel();
        int subLevel = progress.getSubLevel();

        // Progression rule
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

        progress.setLevel(level);
        progress.setSubLevel(subLevel);

        progressRepository.save(progress);

        return new ProgressResponse(
                phoneme,
                level,
                subLevel
        );
    }
}
