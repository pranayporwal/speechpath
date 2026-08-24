package com.example.speechpath;

import android.content.Intent;
import android.os.Bundle;
import android.widget.ArrayAdapter;
import android.widget.Spinner;

import androidx.appcompat.app.AppCompatActivity;

/**
 * Allows the user to select the phoneme they want
 * to practice.
 *
 * Flow:
 *
 * User selects phoneme
 *       ↓
 * PracticeActivity
 *       ↓
 * Selected phoneme determines practice words
 */
public class PhonemeSelectionActivity
        extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        setContentView(
                R.layout.activity_phoneme_selection
        );

        Spinner spinner =
                findViewById(R.id.spinnerPhoneme);

        // Phonemes currently supported by the application.
        String[] phonemes = {
                "Select Phoneme",
                "/sh/",
                "/r/",
                "/l/",
                "/th/",
                "/s/",
                "/z/"
        };

        ArrayAdapter<String> adapter =
                new ArrayAdapter<>(
                        this,
                        android.R.layout
                                .simple_spinner_dropdown_item,
                        phonemes
                );

        spinner.setAdapter(adapter);


        spinner.setOnItemSelectedListener(
                new android.widget.AdapterView
                        .OnItemSelectedListener() {

                    @Override
                    public void onItemSelected(
                            android.widget.AdapterView<?> parent,
                            android.view.View view,
                            int position,
                            long id
                    ) {

                        // Ignore the placeholder option.
                        if (position == 0) {
                            return;
                        }

                        // Open the practice screen.
                        Intent intent =
                                new Intent(
                                        PhonemeSelectionActivity.this,
                                        PracticeActivity.class
                                );

                        // Pass the selected phoneme.
                        intent.putExtra(
                                "phoneme",
                                phonemes[position]
                        );

                        startActivity(intent);
                    }


                    @Override
                    public void onNothingSelected(
                            android.widget.AdapterView<?> parent
                    ) {
                        // Nothing to do.
                    }
                }
        );
    }
}