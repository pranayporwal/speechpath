package com.example.speechpath;

import java.util.List;

/**
 * Represents a phoneme and the practice words
 * associated with that phoneme.
 *
 * Example:
 *
 * /sh/ → ship, shoe, shell, shop
 */
public class PhonemeData {

    private final String symbol;
    private final List<String> words;

    public PhonemeData(
            String symbol,
            List<String> words
    ) {
        this.symbol = symbol;
        this.words = words;
    }

    public String getSymbol() {
        return symbol;
    }

    public List<String> getWords() {
        return words;
    }
}