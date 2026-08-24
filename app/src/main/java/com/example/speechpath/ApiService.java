package com.example.speechpath;

import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import retrofit2.Call;
import retrofit2.http.Multipart;
import retrofit2.http.POST;
import retrofit2.http.Part;

/**
 * Defines the HTTP API used by the Android application.
 *
 * Data flow:
 * Android → Spring Boot → FastAPI
 *
 * The /assess endpoint accepts:
 * - audio: recorded WAV file
 * - expectedPhrase: phrase the user was expected to say
 *
 * The response is converted into a ScoreResponse object.
 */
public interface ApiService {

    /**
     * Sends the recorded audio and expected phrase
     * to the Spring Boot assessment endpoint.
     */
    @Multipart
    @POST("assess")
    Call<ScoreResponse> uploadAudio(
            @Part MultipartBody.Part audio,
            @Part("expectedPhrase") RequestBody expectedText
    );
}
