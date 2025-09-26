from nltk.corpus import words, wordnet as wn


def get_wordset():
    # Use WordNet lemmas which include inflected forms
    wn_lemmas: set[str] = {
        lemma.name().upper() for syn in wn.all_synsets() for lemma in syn.lemmas()
    }

    # Use NTLK words for uncommon words
    nltk_words = set(w.upper() for w in words.words())

    # Combine both wordsets
    wordset = nltk_words | wn_lemmas

    # Filter out words containing characters other than A-Z
    wordset = {word for word in wordset if word.isalpha() and word.isascii()}

    return wordset
