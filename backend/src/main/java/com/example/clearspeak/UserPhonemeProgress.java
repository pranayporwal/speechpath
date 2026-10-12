package com.example.clearspeak;

import jakarta.persistence.*;

@Entity
@Table(name = "user_phoneme_progress")
@IdClass(UserPhonemeProgressId.class)
public class UserPhonemeProgress {

    @Id
    @Column(name = "user_id")
    private Long userId;

    @Id
    @Column(name = "phoneme")
    private String phoneme;

    @Column(name = "level", nullable = false)
    private int level;

    @Column(name = "sub_level", nullable = false)
    private int subLevel;

    public UserPhonemeProgress() {
    }

    public UserPhonemeProgress(
            Long userId,
            String phoneme,
            int level,
            int subLevel
    ) {
        this.userId = userId;
        this.phoneme = phoneme;
        this.level = level;
        this.subLevel = subLevel;
    }
    public void setUserId(Long userId) {
        this.userId = userId;
    }
    public Long getUserId() {
        return userId;
    }
    public void setPhoneme(String phoneme) {
        this.phoneme = phoneme;
    }

    public String getPhoneme() {
        return phoneme;
    }

    public int getLevel() {
        return level;
    }

    public int getSubLevel() {
        return subLevel;
    }

    public void setLevel(int level) {
        this.level = level;
    }

    public void setSubLevel(int subLevel) {
        this.subLevel = subLevel;
    }
}
