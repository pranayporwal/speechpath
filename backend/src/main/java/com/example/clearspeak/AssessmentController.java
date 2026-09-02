package com.example.clearspeak;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/assess")
@CrossOrigin(origins = "*")
public class AssessmentController {

    private final RestTemplate restTemplate;

    @Value("${python.service.url}")
    private String pythonServiceUrl;

    public AssessmentController(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<String> assess(
            @RequestParam("audio") MultipartFile audio,
            @RequestParam("expectedPhrase") String expectedPhrase
    ) {

        try {

            MultiValueMap<String, Object> body =
                    new LinkedMultiValueMap<>();

            // Python expects "expected_phrase"
            body.add("expected_phrase", expectedPhrase);

            // Add audio
            ByteArrayResource audioResource =
                    new ByteArrayResource(audio.getBytes()) {

                        @Override
                        public String getFilename() {
                            return audio.getOriginalFilename();
                        }
                    };

            body.add("audio", audioResource);

            // Headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            HttpEntity<MultiValueMap<String, Object>> request =
                    new HttpEntity<>(body, headers);

            // Forward request to Python
            ResponseEntity<String> response =
                    restTemplate.postForEntity(
                            pythonServiceUrl,
                            request,
                            String.class
                    );

            // Return Python response directly
            return ResponseEntity
                    .status(response.getStatusCode())
                    .body(response.getBody());

        } catch (Exception e) {

            return ResponseEntity
                    .status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("{\"error\":\"Failed to process assessment\"}");
        }
    }
}