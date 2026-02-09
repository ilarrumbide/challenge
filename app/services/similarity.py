from rapidfuzz.distance import JaroWinkler

from app.services.normalizer import normalize


def jaro_winkler_similarity(s1: str, s2: str) -> float:
    """
    Calculate Jaro-Winkler similarity between two strings.

    Uses RapidFuzz's optimized C++ implementation (10-50x faster than pure Python).

    Args:
        s1: First string
        s2: Second string

    Returns:
        Jaro-Winkler similarity score between 0.0 and 1.0
    """
    return JaroWinkler.similarity(s1, s2)


def calculate_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity percentage between two names.

    Normalizes both names before comparison using Jaro-Winkler.

    Args:
        name1: First name
        name2: Second name

    Returns:
        Similarity percentage (0-100)
    """
    n1 = normalize(name1)
    n2 = normalize(name2)

    if n1 == n2:
        return 100.0

    return JaroWinkler.similarity(n1, n2) * 100
