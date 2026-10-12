package com.example.clearspeak;

import java.io.Serializable;
import java.util.Objects;

public class UserPhonemeProgressId
        implements Serializable {

    private Long userId;
    private String phoneme;

    public UserPhonemeProgressId() {
    }

    public UserPhonemeProgressId(
            Long userId,
            String phoneme
    ) {
        this.userId = userId;
        this.phoneme = phoneme;
    }

    @Override
    public boolean equals(Object o) {

        if (this == o) {
            return true;
        }

        if (!(o instanceof UserPhonemeProgressId)) {
            return false;
        }

        UserPhonemeProgressId that =
                (UserPhonemeProgressId) o;

        return Objects.equals(userId, that.userId)
                && Objects.equals(
                phoneme,
                that.phoneme
        );
    }

    @Override
    public int hashCode() {

        return Objects.hash(
                userId,
                phoneme
        );
    }
}