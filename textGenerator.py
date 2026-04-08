import random

POS_WORDS = {
    "DET": ["the", "a", "an", "this", "that", "these", "those"],
    "NOUN": [
        "person", "people", "man", "woman", "child", "children", "boy", "girl", "family", "friend",
        "time", "year", "day", "week", "month", "hour", "minute", "second", "morning", "afternoon",
        "evening", "night", "thing", "place", "house", "home", "room", "door", "window", "street",
        "city", "country", "world", "water", "fire", "earth", "sky", "sun", "moon", "star",
        "tree", "plant", "flower", "animal", "dog", "cat", "bird", "fish", "car", "truck", "bus",
        "train", "plane", "boat", "ship", "school", "church", "store", "market", "restaurant", "office",
        "book", "paper", "pen", "desk", "table", "chair", "bed", "food", "water", "coffee", "tea",
        "bread", "meat", "fruit", "vegetable", "milk", "cheese", "egg", "rice", "pasta", "soup",
        "money", "price", "cost", "dollar", "cent", "phone", "computer", "television", "radio", "music",
        "song", "dance", "game", "sport", "team", "ball", "work", "job", "business", "company",
        "problem", "solution", "question", "answer", "reason", "cause", "effect", "idea", "thought",
        "number", "letter", "word", "name", "color", "size", "shape", "weight", "height", "speed",
        "temperature", "weather", "rain", "snow", "wind", "cloud", "thunder", "lightning", "storm",
        "energy", "power", "force", "motion", "light", "sound", "heat", "cold", "pain", "pleasure",
        "feeling", "emotion", "anger", "joy", "sadness", "fear", "hope", "love", "hate", "trust",
        "doubt", "knowledge", "wisdom", "truth", "lie", "story", "history", "future", "past", "present",
    ],
    "VERB": [
        "go", "come", "say", "make", "get", "know", "think", "see", "find", "give", "tell", "work",
        "call", "try", "ask", "need", "feel", "become", "leave", "put", "mean", "keep", "let", "begin",
        "seem", "help", "talk", "turn", "start", "show", "hear", "play", "run", "move", "like", "live",
        "believe", "hold", "bring", "happen", "write", "provide", "sit", "stand", "lose", "pay", "meet",
        "include", "continue", "set", "learn", "change", "lead", "understand", "watch", "follow", "stop",
        "create", "speak", "read", "allow", "add", "spend", "grow", "open", "walk", "win", "offer",
        "remember", "love", "consider", "appear", "buy", "wait", "serve", "eat", "drink", "sleep", "wake",
    ],
    "ADJ": [
        "good", "bad", "big", "small", "large", "little", "new", "old", "young", "first", "last",
        "long", "short", "high", "low", "fast", "slow", "hot", "cold", "warm", "cool", "wet", "dry",
        "clean", "dirty", "bright", "dark", "light", "heavy", "soft", "hard", "easy", "difficult",
        "simple", "complex", "happy", "sad", "angry", "calm", "quiet", "loud", "strong", "weak",
        "rich", "poor", "smart", "stupid", "beautiful", "ugly", "pretty", "handsome", "kind", "mean",
        "gentle", "rough", "deep", "shallow", "wide", "narrow", "thick", "thin", "full", "empty",
        "sweet", "bitter", "sour", "salty", "delicious", "terrible", "wonderful", "awful", "amazing",
        "boring", "interesting", "funny", "serious", "silly", "wise", "foolish", "brave", "cowardly",
        "honest", "dishonest", "faithful", "unfaithful", "lazy", "active", "quick", "careful", "careless",
        "useful", "useless", "possible", "impossible", "real", "fake", "true", "false", "common", "rare",
        "normal", "strange", "familiar", "foreign", "native", "wild", "tame", "fierce", "peaceful",
        "dangerous", "safe", "healthy", "sick", "alive", "dead", "awake", "asleep", "busy", "free",
    ],
    "ADV": [
        "very", "really", "quite", "just", "only", "also", "too", "so", "well", "better", "best",
        "quickly", "slowly", "carefully", "suddenly", "finally", "already", "still", "again", "always",
        "never", "often", "sometimes", "usually", "rarely", "today", "tomorrow", "yesterday", "now", "then",
        "soon", "late", "early", "forward", "backward", "here", "there", "badly", "worse", "worst",
    ],
    "PREP": [
        "in", "on", "at", "to", "for", "of", "with", "by", "from", "as", "about", "above", "after",
        "before", "between", "during", "through", "under", "over", "around", "against", "among", "along",
        "across", "behind", "beside", "beyond", "down", "up", "out", "into", "onto", "off", "away", "back",
    ],
    "CONJ": ["and", "or", "but", "because", "since", "while", "when", "if", "unless", "until", "though"],
    "AUX": ["is", "was", "are", "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "must", "can"],
}
SENTENCE_TEMPLATES = [
    ["DET", "NOUN", "VERB", "DET", "NOUN"],
    ["DET", "ADJ", "NOUN", "VERB", "DET", "NOUN"],
    ["DET", "NOUN", "VERB", "ADV", "DET", "NOUN"],
    ["DET", "NOUN", "VERB", "DET", "NOUN", "PREP", "DET", "NOUN"],
    ["DET", "NOUN", "AUX", "ADJ"],
    ["DET", "NOUN", "AUX", "VERB", "DET", "NOUN"],
    ["DET", "ADJ", "NOUN", "VERB", "DET", "NOUN", "CONJ", "DET", "NOUN", "VERB"],
]


def select_random_word(pos_tag):
    if pos_tag in POS_WORDS:
        return random.choice(POS_WORDS[pos_tag])
    return ""


def generate_sentence():
    template = random.choice(SENTENCE_TEMPLATES)
    words = [select_random_word(pos) for pos in template]

    sentence = " ".join(words)
    sentence = sentence[0].upper() + sentence[1:] + "."
    return sentence


def generate_mixed_text(length=50):
    """Generate multiple sentences to reach approximately the desired word count.

    Args:
        length: Target number of words (default: 50)

    Returns:
        String of sentences that approximates the target word count
    """
    sentences = []
    current_word_count = 0

    while current_word_count < length:
        sentence = generate_sentence()
        sentences.append(sentence)
        # Count words in the sentence (excluding punctuation)
        words_in_sentence = [w for w in sentence.replace(".", "").split() if w]
        word_count = len(words_in_sentence)
        current_word_count += word_count

    text = " ".join(sentences)

    # Trim sentences if we exceeded target word count significantly
    # Split by sentence (on periods) to preserve punctuation structure
    words_needed = length
    result_sentences = []
    total_words = 0

    for sentence in sentences:
        # Count words in this sentence (without punctuation)
        sentence_words = [w for w in sentence.replace(".", "").split() if w]
        sentence_word_count = len(sentence_words)

        if total_words + sentence_word_count <= words_needed:
            # Include the full sentence
            result_sentences.append(sentence)
            total_words += sentence_word_count
        else:
            # We need to trim this sentence
            remaining_words = words_needed - total_words
            if remaining_words > 0:
                # Include partial sentence
                words_in_sentence = [w for w in sentence.replace(".", "").split() if w]
                trimmed_words = words_in_sentence[:remaining_words]
                result_sentences.append(" ".join(trimmed_words) + ".")
            break

    return " ".join(result_sentences).strip()




