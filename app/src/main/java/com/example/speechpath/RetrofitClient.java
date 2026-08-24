package com.example.speechpath;

import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

/**
 * Creates and provides the Retrofit API client used by the Android app.
 *
 * The Android app sends requests to Spring Boot, which then forwards
 * the request to the Python FastAPI service.
 *
 * Android → Spring Boot :8080 → FastAPI :8000
 */
public class RetrofitClient {

    // 10.0.2.2 points to the host machine from the Android emulator.
    private static final String BASE_URL =
            "http://10.0.2.2:8080/";

    // Single Retrofit instance shared by the application.
    private static final Retrofit retrofit =
            new Retrofit.Builder()
                    .baseUrl(BASE_URL)
                    .addConverterFactory(
                            GsonConverterFactory.create()
                    )
                    .build();

    // Retrofit implementation of our ApiService interface.
    public static final ApiService apiService =
            retrofit.create(ApiService.class);
}