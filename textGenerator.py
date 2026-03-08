import random

SAMPLE_TEXTS = [
    "The quick brown fox jumps over the lazy dog. This pangram contains every letter of the alphabet.",
    "Technology has revolutionized the way we communicate, work, and connect with one another globally.",
    "In the heart of the forest, ancient trees stand as silent guardians of countless generations.",
    "Programming is the art of telling another human what you want the computer to do.",
    "The early morning light filtered through the trees, casting long shadows on the forest floor.",
    "Innovation requires courage, persistence, and a willingness to embrace change and uncertainty.",
    "Music has the power to transcend language barriers and touch the deepest parts of our souls.",
    "Every challenge is an opportunity in disguise, pushing us to grow and become stronger.",
    "The ocean's waves crash against the shore with rhythmic persistence, eroding rock into sand.",
    "A journey of a thousand miles begins with a single step forward into the unknown.",
    "Reading opens doors to worlds beyond our imagination, expanding our knowledge and perspective.",
    "The art of writing requires both clarity of thought and precision in word choice and expression.",
    "Success is not final, failure is not fatal: it is the courage to continue that counts.",
    "The future belongs to those who believe in the beauty of their dreams and work toward them.",
    "Nature has its own rhythm, and learning to move with it brings peace and harmony.",
    "Curiosity is the engine of achievement and the foundation of all scientific progress.",
    "Time moves slowly when you wait for something, but quickly when you are having fun.",
    "Learning a new skill requires patience, practice, and a willingness to make mistakes.",
    "The stars above us tell stories of distant worlds and the vastness of the universe.",
    "In every moment, we have the power to choose our attitude and shape our destiny.",
]


def get_random_sample_text(length=250):
    text = random.choice(SAMPLE_TEXTS)

    while len(text) < length:
        text += " " + random.choice(SAMPLE_TEXTS)

    if len(text) > length:
        trimmed = text[:length]

        for i in range(len(trimmed) - 1, -1, -1):
            if trimmed[i] in '.!?' and (i == len(trimmed) - 1 or trimmed[i + 1] == ' '):
                text = trimmed[:i + 1]
                return text.strip()

        text = trimmed.rsplit(" ", 1)[0]

    return text.strip()


def generate_mixed_text(length=250):
    return get_random_sample_text(length)


