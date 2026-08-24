package com.example.speechpath;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;

import androidx.appcompat.app.AppCompatActivity;

/**
 * Entry point of the ClearSpeak application.
 *
 * The user starts the pronunciation practice flow
 * from this screen.
 *
 * Flow:
 * MainActivity
 *      ↓
 * PhonemeSelectionActivity
 */
public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        setContentView(R.layout.activity_main);

        Button btnStart =
                findViewById(R.id.btnStart);

        // Start the phoneme selection screen.
        btnStart.setOnClickListener(v -> {

            Intent intent =
                    new Intent(
                            MainActivity.this,
                            PhonemeSelectionActivity.class
                    );

            startActivity(intent);
        });
    }
}
