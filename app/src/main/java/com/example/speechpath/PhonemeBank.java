package com.example.speechpath;

import java.util.Arrays;
import java.util.List;

/**
 * Central repository of phonemes and their practice words.
 *
 * This class provides the words used by the practice screen
 * based on the phoneme selected by the user.
 */
public class PhonemeBank {

    private static final List<PhonemeData> phonemes =
            Arrays.asList(

                    new PhonemeData(
                            "/sh/",
                            Arrays.asList(
                                    "ship",
                                    "shoe",
                                    "shell",
                                    "shop"
                            )
                    ),

                    new PhonemeData(
                            "/r/",
                            Arrays.asList(
                                    "red",
                                    "run",
                                    "rice",
                                    "rope"
                            )
                    ),

                    new PhonemeData(
                            "/l/",
                            Arrays.asList(
                                    "lamp",
                                    "lake",
                                    "leaf",
                                    "lock"
                            )
                    ),

                    new PhonemeData(
                            "/th/",
                            Arrays.asList(
                                    "three",
                                    "think",
                                    "throw",
                                    "thank"
                            )
                    ),

                    new PhonemeData(
                            "/s/",
                            Arrays.asList(
                                    "sun",
                                    "sand",
                                    "sock",
                                    "salt"
                            )
                    ),

                    new PhonemeData(
                            "/z/",
                            Arrays.asList(
                                    "zoo",
                                    "zero",
                                    "zip",
                                    "zone"
                            )
                    )
            );

    /**
     * Returns the practice words associated with a phoneme.
     *
     * If the phoneme isn't found, "ship" is used as
     * the default practice word.
     */
    public static List<String> getWords(String symbol) {

        for (PhonemeData phoneme : phonemes) {

            if (phoneme.getSymbol().equals(symbol)) {
                return phoneme.getWords();
            }
        }

        return Arrays.asList("ship");
    }
}