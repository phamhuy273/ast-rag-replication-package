"""tests/test_cache_invalidation.py - Verifies hash-locked cache validation and invalidation.

Governed by Rules R27 and R28 of the Anti-Hardcoding Specification:
Cache must be strictly keyed by the composite hash of inputs (corpus text, model ID, max_seq_length).
Changing any input must invalidate and discard the cache.
"""

import hashlib
import json
import pytest


def compute_cache_key(texts, model_name="BAAI/bge-m3", max_seq_length=512):
    """Derive deterministic cache signature from inputs per Rule R27."""
    hasher = hashlib.sha256()
    hasher.update(model_name.encode("utf-8"))
    hasher.update(str(max_seq_length).encode("utf-8"))
    for t in texts:
        hasher.update(t.encode("utf-8"))
    return hasher.hexdigest()


def validate_cache(cache_metadata, current_texts, model_name="BAAI/bge-m3", max_seq_length=512):
    """Validate cache per Rule R28: verify item count and input hash match current data."""
    if cache_metadata.get("count") != len(current_texts):
        return False, "Count mismatch"
    current_key = compute_cache_key(current_texts, model_name, max_seq_length)
    if cache_metadata.get("input_hash") != current_key:
        return False, "Input hash mismatch"
    return True, "Valid"


class TestCacheInvalidation:
    """Verifies that caching logic strictly obeys Rules R27 and R28."""

    def test_cache_key_changes_on_text_modification(self):
        texts_v1 = ["public void process() { ... }", "class Repository { ... }"]
        texts_v2 = ["public void process() { /* edit */ }", "class Repository { ... }"]

        key1 = compute_cache_key(texts_v1)
        key2 = compute_cache_key(texts_v2)

        assert key1 != key2, "Cache key must change when text content changes (R27)"

    def test_cache_key_changes_on_model_or_param_change(self):
        texts = ["public void process() { ... }"]
        key_bge = compute_cache_key(texts, model_name="BAAI/bge-m3", max_seq_length=512)
        key_diff_model = compute_cache_key(texts, model_name="sentence-transformers/all-MiniLM-L6-v2", max_seq_length=512)
        key_diff_seq = compute_cache_key(texts, model_name="BAAI/bge-m3", max_seq_length=256)

        assert key_bge != key_diff_model, "Cache key must change when model changes (R27)"
        assert key_bge != key_diff_seq, "Cache key must change when max_seq_length changes (R27)"

    def test_cache_validation_rejects_stale_data(self):
        texts_initial = ["item 1", "item 2", "item 3"]
        initial_key = compute_cache_key(texts_initial)
        metadata = {
            "count": len(texts_initial),
            "input_hash": initial_key
        }

        # Valid case
        is_valid, msg = validate_cache(metadata, texts_initial)
        assert is_valid is True

        # Stale text case
        texts_modified = ["item 1", "item 2 modified", "item 3"]
        is_valid, msg = validate_cache(metadata, texts_modified)
        assert is_valid is False
        assert msg == "Input hash mismatch"

        # Stale count case (e.g. filtered dataset)
        texts_truncated = ["item 1", "item 2"]
        is_valid, msg = validate_cache(metadata, texts_truncated)
        assert is_valid is False
        assert msg == "Count mismatch"
