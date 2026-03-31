import random

WORDS = [
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "as", "is", "was", "are", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "must", "can", "that", "this", "these", "those",
    "go", "come", "say", "said", "make", "made", "get", "got", "know", "think", "see", "find",
    "give", "tell", "work", "call", "try", "ask", "need", "feel", "become", "leave", "put", "mean",
    "keep", "let", "begin", "seem", "help", "talk", "turn", "start", "show", "hear", "play", "run",
    "move", "like", "live", "believe", "hold", "bring", "happen", "write", "provide", "sit", "stand",
    "lose", "pay", "meet", "include", "continue", "set", "learn", "change", "lead", "understand",
    "watch", "follow", "stop", "create", "speak", "read", "allow", "add", "spend", "grow", "open",
    "walk", "win", "offer", "remember", "love", "consider", "appear", "buy", "wait", "serve",
    "person", "people", "man", "woman", "child", "children", "boy", "girl", "family", "friend",
    "time", "year", "day", "week", "month", "hour", "minute", "second", "morning", "afternoon",
    "evening", "night", "thing", "place", "house", "home", "room", "door", "window", "street",
    "city", "country", "world", "water", "fire", "earth", "sky", "sun", "moon", "star",
    "tree", "plant", "flower", "animal", "dog", "cat", "bird", "fish", "car", "truck", "bus",
    "train", "plane", "boat", "ship", "school", "church", "store", "market", "restaurant", "office",
    "book", "paper", "pen", "desk", "table", "chair", "bed", "food", "water", "coffee", "tea",
    "bread", "meat", "fruit", "vegetable", "milk", "cheese", "egg", "rice", "pasta", "soup",
    "money", "price", "cost", "dollar", "cent", "phone", "computer", "television", "radio", "music",
    "song", "dance", "game", "sport", "team", "game", "ball", "work", "job", "business", "company",
    "problem", "solution", "question", "answer", "reason", "cause", "effect", "idea", "thought",
    "number", "letter", "word", "name", "color", "size", "shape", "weight", "height", "speed",
    "temperature", "weather", "rain", "snow", "wind", "cloud", "thunder", "lightning", "storm",
    "energy", "power", "force", "motion", "light", "sound", "heat", "cold", "pain", "pleasure",
    "feeling", "emotion", "anger", "joy", "sadness", "fear", "hope", "love", "hate", "trust",
    "doubt", "knowledge", "wisdom", "truth", "lie", "story", "history", "future", "past", "present",
    "good", "bad", "big", "small", "large", "little", "new", "old", "young", "first", "last",
    "long", "short", "high", "low", "fast", "slow", "hot", "cold", "warm", "cool", "wet", "dry",
    "clean", "dirty", "bright", "dark", "light", "heavy", "soft", "hard", "easy", "difficult",
    "simple", "complex", "happy", "sad", "angry", "calm", "quiet", "loud", "strong", "weak",
    "rich", "poor", "smart", "stupid", "beautiful", "ugly", "pretty", "handsome", "kind", "mean",
    "gentle", "rough", "deep", "shallow", "wide", "narrow", "thick", "thin", "full", "empty",
    "quiet", "noisy", "sweet", "bitter", "sour", "salty", "delicious", "terrible", "wonderful",
    "awful", "amazing", "boring", "interesting", "funny", "serious", "silly", "wise", "foolish",
    "brave", "cowardly", "honest", "dishonest", "faithful", "unfaithful", "lazy", "active", "slow",
    "quick", "careful", "careless", "useful", "useless", "possible", "impossible", "real", "fake",
    "true", "false", "common", "rare", "normal", "strange", "familiar", "foreign", "native",
    "wild", "tame", "gentle", "fierce", "calm", "excited", "relaxed", "tense", "peaceful",
    "dangerous", "safe", "healthy", "sick", "alive", "dead", "awake", "asleep", "busy", "free",
    "very", "really", "quite", "just", "only", "also", "too", "so", "such", "more", "most",
    "less", "least", "well", "better", "best", "badly", "worse", "worst", "quickly", "slowly",
    "carefully", "suddenly", "finally", "already", "still", "again", "always", "never", "often",
    "sometimes", "usually", "rarely", "here", "there", "where", "when", "why", "how", "today",
    "tomorrow", "yesterday", "now", "then", "soon", "late", "early", "forward", "backward",
    "about", "above", "after", "before", "between", "during", "through", "under", "over", "around",
    "against", "among", "along", "across", "behind", "beside", "beyond", "down", "up", "out",
    "into", "onto", "off", "away", "back", "down", "up", "out", "over", "under", "through",
    "because", "since", "while", "when", "where", "why", "how", "which", "who", "whom", "what",
    "whose", "if", "unless", "until", "till", "though", "although", "even", "else", "neither",
    "nor", "either", "nor", "both", "all", "each", "every", "either", "neither", "some", "any",
    "much", "many", "few", "more", "most", "less", "least", "several", "various", "certain",
    "different", "same", "other", "another", "such", "same", "kind", "type", "sort", "way",
    "means", "method", "process", "system", "order", "rule", "law", "right", "wrong", "duty",
    "responsibility", "freedom", "liberty", "justice", "peace", "war", "battle", "conflict",
    "agreement", "disagreement", "success", "failure", "victory", "defeat", "win", "loss",
]


def generate_mixed_text(length=250):
    words = []
    current_length = 0

    while current_length < length:
        word = random.choice(WORDS)
        words.append(word)
        # Account for the space between words
        current_length += len(word) + 1

    text = " ".join(words)

    # Trim to approximate length
    if len(text) > length:
        text = text[:length].rsplit(" ", 1)[0]

    return text.strip()

