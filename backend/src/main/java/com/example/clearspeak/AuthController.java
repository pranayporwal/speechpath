package com.example.clearspeak;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final UserRepository userRepository;

    public AuthController(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(
            @RequestBody LoginRequest request
    ) {

        if (request.username() == null
                || request.username().trim().isEmpty()) {

            return ResponseEntity.badRequest().build();
        }

        String username =
                request.username().trim();

        User user =
                userRepository
                        .findByUsername(username)
                        .orElseGet(() ->
                                userRepository.save(
                                        new User(username)
                                )
                        );

        return ResponseEntity.ok(
                new LoginResponse(
                        user.getId(),
                        user.getUsername()
                )
        );
    }
}
