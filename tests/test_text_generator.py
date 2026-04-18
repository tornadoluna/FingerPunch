"""tests for textGenerator module."""
from textGenerator import POS_WORDS, select_random_word, generate_sentence, generate_mixed_text
def test_pos_words_exists():
    """Test that POS_WORDS exists and has content."""
    assert len(POS_WORDS) > 0
    assert 'NOUN' in POS_WORDS
    assert 'VERB' in POS_WORDS
def test_select_random_word():
    """Test select_random_word function."""
    word = select_random_word('NOUN')
    assert isinstance(word, str)
    assert len(word) > 0
    assert word in POS_WORDS['NOUN']
def test_select_invalid_pos():
    """Test select_random_word with invalid POS tag."""
    word = select_random_word('INVALID')
    assert word == ''
def test_generate_sentence():
    """Test generate_sentence function."""
    sentence = generate_sentence()
    assert isinstance(sentence, str)
    assert len(sentence) > 0
    assert sentence.endswith('.')
    assert sentence[0].isupper()
def test_generate_mixed_text():
    """Test generate_mixed_text function."""
    text = generate_mixed_text(length=5)
    assert isinstance(text, str)
    assert len(text) > 0
    # Count words
    words = []
    for sentence in text.split('.'):
        sentence = sentence.strip()
        if sentence:
            words.extend([w for w in sentence.split() if w])
    assert len(words) >= 3  # Should have at least a few words
