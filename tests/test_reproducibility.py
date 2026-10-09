"""tests/test_reproducibility.py - Determinism and seed consistency tests.

Governed by Rule R33 of the Anti-Hardcoding Specification:
Ensure statistical operations (bootstrap CI, permutation test, sampling) produce strictly identical
numerical results when run with the fixed random seed (42).
"""

import numpy as np
import pytest


def run_bootstrap_ci(diffs, n_resamples=1000, seed=42):
    """Compute 95% bootstrap confidence interval with fixed random seed."""
    rng = np.random.default_rng(seed)
    diffs = np.asarray(diffs, dtype=float)
    n = len(diffs)
    boot_means = np.empty(n_resamples)
    for i in range(n_resamples):
        sample = rng.choice(diffs, size=n, replace=True)
        boot_means[i] = np.mean(sample)
    ci_lower = float(np.percentile(boot_means, 2.5))
    ci_upper = float(np.percentile(boot_means, 97.5))
    return float(np.mean(diffs)), ci_lower, ci_upper


def run_permutation_test(scores_a, scores_b, n_permutations=1000, seed=42):
    """Compute permutation test p-value with fixed random seed."""
    rng = np.random.default_rng(seed)
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    obs_diff = np.mean(a - b)
    diffs = np.empty(n_permutations)
    pooled = np.column_stack([a, b])
    for i in range(n_permutations):
        # randomly flip signs of differences
        signs = rng.choice([-1, 1], size=len(a))
        diffs[i] = np.mean((a - b) * signs)
    p_val = float(np.mean(np.abs(diffs) >= np.abs(obs_diff)))
    return obs_diff, p_val


class TestReproducibility:
    """Verifies that randomized statistical operations are 100% deterministic under fixed seeds (R33)."""

    def test_bootstrap_determinism(self):
        fake_data = [0.12, -0.05, 0.22, 0.15, 0.08, -0.02, 0.19, 0.11, 0.05, 0.14] * 2

        mean1, low1, high1 = run_bootstrap_ci(fake_data, n_resamples=1000, seed=42)
        mean2, low2, high2 = run_bootstrap_ci(fake_data, n_resamples=1000, seed=42)

        assert mean1 == mean2
        assert low1 == low2
        assert high1 == high2

    def test_permutation_test_determinism(self):
        a = [0.8, 0.75, 0.9, 0.85, 0.7, 0.95, 0.88, 0.82, 0.79, 0.91]
        b = [0.7, 0.65, 0.8, 0.75, 0.68, 0.85, 0.78, 0.72, 0.71, 0.80]

        diff1, p1 = run_permutation_test(a, b, n_permutations=1000, seed=42)
        diff2, p2 = run_permutation_test(a, b, n_permutations=1000, seed=42)

        assert diff1 == diff2
        assert p1 == p2
