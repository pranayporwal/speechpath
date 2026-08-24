package com.example.speechpath;

import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

import java.io.File;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Handles communication between the PracticeActivity and the backend.
 *
 * Responsibilities:
 * 1. Convert the recorded WAV file into a multipart request.
 * 2. Add the expected phrase to the request.
 * 3. Send the request through Retrofit.
 * 4. Store the assessment result for the UI.
 *
 * Data flow:
 * PracticeActivity
 *       ↓
 * ScoreViewModel
 *       ↓
 * Retrofit / ApiService
 *       ↓
 * Spring Boot → FastAPI
 *       ↓
 * ScoreResponse
 */
public class ScoreViewModel extends ViewModel {

    // Holds the successful assessment result for the Activity to observe.
    private final MutableLiveData<ScoreResponse> scoreResult =
            new MutableLiveData<>();

    // Holds an error message if the request fails.
    private final MutableLiveData<String> errorMessage =
            new MutableLiveData<>();

    public MutableLiveData<ScoreResponse> getScoreResult() {
        return scoreResult;
    }

    public MutableLiveData<String> getErrorMessage() {
        return errorMessage;
    }

    /**
     * Uploads the recorded WAV file and expected phrase
     * to the Spring Boot backend.
     */
    public void uploadWavFile(
            File wavFile,
            String expectedText
    ) {

        // Convert the WAV file into an HTTP request body.
        RequestBody requestFile =
                RequestBody.create(
                        MediaType.parse("audio/wav"),
                        wavFile
                );

        // Add the file to the multipart request.
        MultipartBody.Part audioPart =
                MultipartBody.Part.createFormData(
                        "audio",
                        wavFile.getName(),
                        requestFile
                );

        // Convert the expected phrase into a text request body.
        RequestBody expectedBody =
                RequestBody.create(
                        MediaType.parse("text/plain"),
                        expectedText
                );

        // Send the request asynchronously through Retrofit.
        Call<ScoreResponse> call =
                RetrofitClient.apiService.uploadAudio(
                        audioPart,
                        expectedBody
                );

        call.enqueue(new Callback<ScoreResponse>() {

            @Override
            public void onResponse(
                    Call<ScoreResponse> call,
                    Response<ScoreResponse> response
            ) {

                if (response.isSuccessful()
                        && response.body() != null) {

                    // Pass the successful result to the UI.
                    scoreResult.postValue(
                            response.body()
                    );

                } else {

                    errorMessage.postValue(
                            "Upload failed: " + response.code()
                    );
                }
            }

            @Override
            public void onFailure(
                    Call<ScoreResponse> call,
                    Throwable t
            ) {

                // Handles network/server connection errors.
                errorMessage.postValue(
                        t.getMessage() != null
                                ? t.getMessage()
                                : "Network error"
                );
            }
        });
    }
}
