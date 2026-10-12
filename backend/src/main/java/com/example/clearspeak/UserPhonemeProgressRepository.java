package com.example.clearspeak;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface UserPhonemeProgressRepository
        extends JpaRepository<
        UserPhonemeProgress,
        UserPhonemeProgressId> {

    List<UserPhonemeProgress> findByUserId(Long userId);
}
