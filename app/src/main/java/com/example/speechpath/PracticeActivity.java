package com.example.speechpath;

import android.Manifest;
import android.content.pm.PackageManager;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.widget.Button;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.lifecycle.ViewModelProvider;

import java.io.File;
import java.io.FileOutputStream;
import java.io.RandomAccessFile;
import java.util.Locale;

/**
 * Main practice screen for speech pronunciation assessment.
 *
 * Responsibilities:
 * 1. Display the current practice word and phoneme.
 * 2. Provide text-to-speech pronunciation.
 * 3. Record the user's voice as a 16 kHz mono WAV file.
 * 4. Send the recording and expected word to ScoreViewModel.
 * 5. Display the transcript and assessment score.
 *
 * Data flow:
 *
 * User speaks
 *     ↓
 * AudioRecord
 *     ↓
 * speech.wav
 *     ↓
 * ScoreViewModel
 *     ↓
 * Spring Boot → FastAPI → Wav2Vec2
 *     ↓
 * ScoreResponse
 *     ↓
 * UI
 */
public class PracticeActivity extends AppCompatActivity {

    private TextView txtFeedback;

    // Words available for the selected phoneme.
    private java.util.List<String> words;

    private int currentWordIndex = 0;

    // Android Text-to-Speech engine.
    private TextToSpeech tts;

    // Handles microphone recording.
    private AudioRecord audioRecord;

    // Background thread that writes microphone data to the WAV file.
    private Thread recordingThread;

    private boolean isRecording = false;

    // Temporary WAV file created by the recording process.
    private File wavFile;

    // Wav2Vec2 expects 16 kHz audio.
    private final int sampleRate = 16000;

    // Mono audio.
    private final int channelConfig =
            AudioFormat.CHANNEL_IN_MONO;

    // 16-bit PCM audio.
    private final int audioFormat =
            AudioFormat.ENCODING_PCM_16BIT;

    // Minimum buffer size required by AudioRecord.
    private final int bufferSize =
            AudioRecord.getMinBufferSize(
                    sampleRate,
                    channelConfig,
                    audioFormat
            );

    // ViewModel handles communication with the backend.
    private ScoreViewModel scoreViewModel;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        setContentView(R.layout.activity_practice);

        // Get the phoneme selected by the previous screen.
        String phoneme =
                getIntent().getStringExtra("phoneme");

        if (phoneme == null) {
            phoneme = "/sh/";
        }

        // Load words associated with the selected phoneme.
        words = PhonemeBank.getWords(phoneme);
        // Initialize the speech synthesis engine.
        tts = new TextToSpeech(this, status -> {

            if (status == TextToSpeech.SUCCESS) {

                tts.setLanguage(
                        new Locale("en", "IN")
                );

                tts.setSpeechRate(0.85f);
            }
        });

        // Create the ViewModel.
        scoreViewModel =
                new ViewModelProvider(this)
                        .get(ScoreViewModel.class);

        // Find UI elements.
        TextView txtPhoneme =
                findViewById(R.id.txtPhoneme);

        TextView txtHint =
                findViewById(R.id.txtHint);

        TextView txtWord =
                findViewById(R.id.txtWord);

        TextView txtScore =
                findViewById(R.id.txtScore);

        txtFeedback =
                findViewById(R.id.txtFeedback);

        Button btnHear =
                findViewById(R.id.btnHear);

        Button btnRecord =
                findViewById(R.id.btnRecord);

        android.widget.ImageButton btnBack =
                findViewById(R.id.btnBack);


        // Display phoneme information.
        txtPhoneme.setText(
                phoneme + " Sound"
        );

        txtHint.setText(
                "Focus on the " + phoneme + " sound"
        );

        // Display the current practice word.
        txtWord.setText(
                words.get(currentWordIndex).toUpperCase()
        );


        // Back button.
        btnBack.setOnClickListener(v -> finish());


        // Hear button uses Text-to-Speech.
        btnHear.setOnClickListener(v -> {

            String word =
                    words.get(currentWordIndex);

            tts.speak(
                    word,
                    TextToSpeech.QUEUE_FLUSH,
                    null,
                    null
            );
        });


        // Record button starts/stops recording.
        btnRecord.setOnClickListener(v -> {

            if (!isRecording) {

                startRecording();

                btnRecord.setText("Stop");

            } else {

                stopRecording();

                btnRecord.setText("Record");

                txtFeedback.setText(
                        "Audio saved successfully"
                );
            }
        });


        // Observe successful assessment results.
        scoreViewModel
                .getScoreResult()
                .observe(this, result -> {

                    txtScore.setText(
                            "Score: "
                                    + result.getScore()
                                    + "%"
                    );

                    txtFeedback.setText(
                            "You said: "
                                    + result.getTranscript()
                                    + "\nExpected: "
                                    + result.getExpected()
                    );
                });


        // Observe network/server errors.
        scoreViewModel
                .getErrorMessage()
                .observe(this, error -> {

                    if (error != null) {
                        txtFeedback.setText(error);
                    }
                });
    }


    /**
     * Starts microphone recording.
     *
     * The recording is configured as:
     * 16 kHz / mono / 16-bit PCM.
     */
    private void startRecording() {

        // Check microphone permission.
        if (ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.RECORD_AUDIO
        ) != PackageManager.PERMISSION_GRANTED) {

            ActivityCompat.requestPermissions(
                    this,
                    new String[]{
                            Manifest.permission.RECORD_AUDIO
                    },
                    100
            );

            return;
        }


        // Create the WAV file inside the app's private storage.
        wavFile = new File(
                getFilesDir(),
                "speech.wav"
        );


        // Create the microphone recorder.
        audioRecord = new AudioRecord(
                MediaRecorder.AudioSource.MIC,
                sampleRate,
                channelConfig,
                audioFormat,
                bufferSize
        );


        // Start recording.
        audioRecord.startRecording();

        runOnUiThread(() ->
                txtFeedback.setText(
                        "Recording started"
                )
        );

        isRecording = true;


        // Write microphone data on a background thread.
        recordingThread = new Thread(
                this::writeAudioToFile
        );

        recordingThread.start();
    }


    /**
     * Stops recording, completes the WAV file,
     * and uploads it for assessment.
     */
    private void stopRecording() {

        isRecording = false;


        // Stop microphone capture.
        if (audioRecord != null) {
            audioRecord.stop();
        }


        /*
         * Wait until the recording thread has finished
         * writing and closing the WAV file.
         */
        if (recordingThread != null) {

            try {
                recordingThread.join();

            } catch (InterruptedException e) {

                Thread.currentThread().interrupt();
            }
        }


        // Release microphone resources.
        if (audioRecord != null) {
            audioRecord.release();
        }

        audioRecord = null;
        recordingThread = null;


        // Update WAV header with the final audio size.
        updateWavHeader(wavFile);


        // Send WAV + expected word to backend.
        scoreViewModel.uploadWavFile(
                wavFile,
                words.get(currentWordIndex)
        );
    }


    /**
     * Continuously reads microphone data and writes
     * it into the WAV file.
     */
    private void writeAudioToFile() {

        byte[] data =
                new byte[bufferSize];


        try {

            FileOutputStream outputStream =
                    new FileOutputStream(wavFile);


            // Write placeholder WAV header.
            writeWavHeader(outputStream);


            while (isRecording) {

                int read =
                        audioRecord.read(
                                data,
                                0,
                                data.length
                        );


                if (read > 0) {

                    outputStream.write(
                            data,
                            0,
                            read
                    );
                }
            }


            outputStream.close();


            runOnUiThread(() ->
                    txtFeedback.setText(
                            "WAV saved"
                    )
            );


        } catch (Exception e) {

            runOnUiThread(() ->
                    txtFeedback.setText(
                            "Recording error: "
                                    + e.getMessage()
                    )
            );
        }
    }


    /**
     * Creates the initial 44-byte WAV header.
     *
     * The actual file size is filled in later by
     * updateWavHeader().
     */
    private void writeWavHeader(
            FileOutputStream outputStream
    ) throws java.io.IOException {

        byte[] header =
                new byte[44];

        int byteRate =
                sampleRate * 2;


        header[0] = 'R';
        header[1] = 'I';
        header[2] = 'F';
        header[3] = 'F';


        header[8] = 'W';
        header[9] = 'A';
        header[10] = 'V';
        header[11] = 'E';


        header[12] = 'f';
        header[13] = 'm';
        header[14] = 't';
        header[15] = ' ';


        header[16] = 16;
        header[20] = 1;
        header[22] = 1;


        header[24] =
                (byte) (sampleRate & 0xff);

        header[25] =
                (byte) ((sampleRate >> 8) & 0xff);


        header[28] =
                (byte) (byteRate & 0xff);

        header[29] =
                (byte) ((byteRate >> 8) & 0xff);


        header[32] = 2;
        header[34] = 16;


        header[36] = 'd';
        header[37] = 'a';
        header[38] = 't';
        header[39] = 'a';


        outputStream.write(
                header,
                0,
                44
        );
    }


    /**
     * Updates the WAV header after recording finishes.
     *
     * WAV files need the final audio size stored in
     * the header before being sent to the backend.
     */
    private void updateWavHeader(File file) {

        long totalAudioLen =
                file.length() - 44;

        long totalDataLen =
                totalAudioLen + 36;


        try {

            RandomAccessFile randomAccessFile =
                    new RandomAccessFile(
                            file,
                            "rw"
                    );


            // Update RIFF chunk size.
            randomAccessFile.seek(4);

            randomAccessFile.writeInt(
                    Integer.reverseBytes(
                            (int) totalDataLen
                    )
            );


            // Update data chunk size.
            randomAccessFile.seek(40);

            randomAccessFile.writeInt(
                    Integer.reverseBytes(
                            (int) totalAudioLen
                    )
            );


            randomAccessFile.close();

        } catch (Exception e) {

            txtFeedback.setText(
                    "WAV error: "
                            + e.getMessage()
            );
        }
    }


    /**
     * Release Text-to-Speech resources when the Activity closes.
     */
    @Override
    protected void onDestroy() {

        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }

        super.onDestroy();
    }
}