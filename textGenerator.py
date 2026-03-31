import random

# Simple word list for generating random text
WORDS = [
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
    "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi",
    "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
    "apple", "banana", "cherry", "dragon", "elephant", "forest", "guitar", "house",
    "island", "jungle", "kitchen", "library", "mountain", "nature", "ocean", "piano",
    "quiet", "river", "silver", "table", "umbrella", "valley", "window", "xylophone",
    "yellow", "zebra", "anchor", "bright", "crystal", "diamond", "energy", "flame",
    "golden", "horizon", "journey", "kingdom", "legacy", "melody", "network", "orbit",
    "palace", "quest", "radiant", "stellar", "triumph", "universe", "vibrant", "wonder",
]


def generate_mixed_text(length=250):
    """Generate a random string of words to reach approximately the desired length."""
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

