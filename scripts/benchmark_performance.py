import time
from typing import Callable

from rapidfuzz.distance import JaroWinkler

# Test data: common Spanish names
TEST_NAMES = [
    ("Juan García López", "juan garcia lopes"),
    ("María Rodríguez", "maria rodriges"),
    ("Pedro Martínez Sánchez", "pedro martinez sanches"),
    ("José González", "jose gonzales"),
    ("Ana Fernández", "ana fernandes"),
    ("Carlos Pérez", "carlos peres"),
    ("Laura Gómez", "laura gomes"),
    ("Miguel Díaz", "miguel dias"),
]


def benchmark_function(func: Callable, iterations: int = 10000) -> float:
    """
    Benchmark a similarity function.

    Args:
        func: Function to benchmark
        iterations: Number of iterations to run

    Returns:
        Elapsed time in seconds
    """
    start = time.perf_counter()
    for _ in range(iterations):
        for name1, name2 in TEST_NAMES:
            func(name1, name2)
    elapsed = time.perf_counter() - start
    return elapsed


def rapidfuzz_similarity(s1: str, s2: str) -> float:
    """RapidFuzz implementation."""
    return JaroWinkler.similarity(s1, s2)


def pure_python_jaro_similarity(s1: str, s2: str) -> float:
    """Pure Python Jaro implementation for comparison."""
    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    match_distance = max(len1, len2) // 2 - 1
    if match_distance < 0:
        match_distance = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0

    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    transpositions = 0
    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    transpositions //= 2
    return (matches / len1 + matches / len2 + (matches - transpositions) / matches) / 3


def pure_python_jaro_winkler(s1: str, s2: str, prefix_weight: float = 0.1) -> float:
    """Pure Python Jaro-Winkler implementation."""
    jaro_sim = pure_python_jaro_similarity(s1, s2)
    prefix_len = 0
    max_prefix = min(len(s1), len(s2), 4)
    for i in range(max_prefix):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break
    return jaro_sim + prefix_len * prefix_weight * (1 - jaro_sim)


if __name__ == "__main__":
    print("=" * 70)
    print("Performance Benchmark: RapidFuzz vs Pure Python")
    print("=" * 70)
    print()

    iterations = 10000
    print(f"Running {iterations} iterations with {len(TEST_NAMES)} name pairs each...")
    print(f"Total comparisons: {iterations * len(TEST_NAMES):,}")
    print()

    # Benchmark RapidFuzz
    print("Benchmarking RapidFuzz (C++ optimized)...")
    rapidfuzz_time = benchmark_function(rapidfuzz_similarity, iterations)
    print(f"  Time: {rapidfuzz_time:.4f} seconds")
    print(f"  Rate: {iterations * len(TEST_NAMES) / rapidfuzz_time:,.0f} comparisons/sec")
    print()

    # Benchmark Pure Python
    print("Benchmarking Pure Python implementation...")
    python_time = benchmark_function(pure_python_jaro_winkler, iterations)
    print(f"  Time: {python_time:.4f} seconds")
    print(f"  Rate: {iterations * len(TEST_NAMES) / python_time:,.0f} comparisons/sec")
    print()

    # Calculate speedup
    speedup = python_time / rapidfuzz_time
    print("=" * 70)
    print(f"SPEEDUP: {speedup:.1f}x faster with RapidFuzz")
    print("=" * 70)
    print()

    # Verify results are similar
    print("Verifying accuracy...")
    for name1, name2 in TEST_NAMES[:3]:
        rf_score = rapidfuzz_similarity(name1, name2)
        py_score = pure_python_jaro_winkler(name1, name2)
        diff = abs(rf_score - py_score)
        print(f"  '{name1}' vs '{name2}'")
        print(f"    RapidFuzz: {rf_score:.4f} | Python: {py_score:.4f} | Diff: {diff:.6f}")
