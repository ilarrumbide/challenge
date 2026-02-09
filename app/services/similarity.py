from rapidfuzz.distance import JaroWinkler

from app.services.normalizer import normalize


def jaro_winkler_similarity(s1: str, s2: str) -> float:
    return JaroWinkler.similarity(s1, s2)


def calculate_similarity(name1: str, name2: str) -> float:
    n1 = normalize(name1)
    n2 = normalize(name2)

    if n1 == n2:
        return 100.0

    return JaroWinkler.similarity(n1, n2) * 100
