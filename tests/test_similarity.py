import pytest

from app.services.similarity import (
    calculate_similarity,
    jaro_winkler_similarity,
)


class TestJaroWinklerSimilarity:
    """Test cases for Jaro-Winkler similarity using RapidFuzz."""

    def test_identical_strings(self):
        assert jaro_winkler_similarity("juan", "juan") == 1.0

    def test_completely_different(self):
        score = jaro_winkler_similarity("abc", "xyz")
        assert score < 0.5

    def test_common_name_variations(self):
        # Common name matching scenarios
        assert jaro_winkler_similarity("garcia", "garsia") > 0.9
        assert jaro_winkler_similarity("gonzalez", "gonzales") > 0.9

    def test_prefix_bonus(self):
        # Names with matching prefixes should score well
        score = jaro_winkler_similarity("martinez", "martines")
        assert score > 0.9

    def test_empty_strings(self):
        # RapidFuzz handles empty strings gracefully
        score1 = jaro_winkler_similarity("juan", "")
        score2 = jaro_winkler_similarity("", "juan")
        assert score1 == 0.0
        assert score2 == 0.0


class TestCalculateSimilarity:
    """Test cases for the main calculate_similarity function."""

    def test_identical_names(self):
        assert calculate_similarity("Juan Garcia", "Juan Garcia") == 100.0

    def test_case_insensitive(self):
        assert calculate_similarity("JUAN GARCIA", "juan garcia") == 100.0

    def test_accent_insensitive(self):
        assert calculate_similarity("María García", "maria garcia") == 100.0

    def test_whitespace_tolerance(self):
        assert calculate_similarity("Juan  García", "Juan García") == 100.0

    def test_typo_tolerance(self):
        # Single character typo should still have high similarity
        score = calculate_similarity("Juan Garcia", "Juan Garsia")
        assert score > 90.0

    def test_similar_names(self):
        score = calculate_similarity("Juan García López", "Juan Garcia Lopez")
        assert score == 100.0  # After normalization they're identical

    def test_different_names(self):
        score = calculate_similarity("Juan García", "Pedro López")
        assert score < 70.0  # Different names, low similarity

    def test_partial_match(self):
        score = calculate_similarity("Juan", "Juan García")
        assert 50.0 < score < 90.0  # Partial match
