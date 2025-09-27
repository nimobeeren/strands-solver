from nltk.corpus import words as nltk_words, wordnet as wn


def get_wordset():
    words: set[str] = set()

    # Use WordNet lemmas which include inflected forms
    words |= set(wn.all_lemma_names())
    # Add NTLK words for uncommon words
    words |= set(nltk_words.words())
    # Convert to uppercase
    # And filter out words containing characters other than A-Z
    words = {word.upper() for word in words if word.isalpha() and word.isascii()}

    return words
