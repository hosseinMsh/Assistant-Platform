"""Tests for token normalization."""
import pytest
from app.core.token import normalize_token


def test_raw_token():
    assert normalize_token("eyJhbGciOiJIUzI1NiJ9") == "eyJhbGciOiJIUzI1NiJ9"

def test_bearer_prefix():
    assert normalize_token("Bearer eyJhbGciOiJIUzI1NiJ9") == "eyJhbGciOiJIUzI1NiJ9"

def test_bearer_upper():
    assert normalize_token("BEARER eyJhbGciOiJIUzI1NiJ9") == "eyJhbGciOiJIUzI1NiJ9"

def test_bearer_mixed_case():
    assert normalize_token("BeArEr eyJhbGciOiJIUzI1NiJ9") == "eyJhbGciOiJIUzI1NiJ9"

def test_leading_trailing_whitespace():
    assert normalize_token("  eyJhbGciOiJIUzI1NiJ9  ") == "eyJhbGciOiJIUzI1NiJ9"

def test_bearer_with_whitespace():
    assert normalize_token("  Bearer   eyJhbGciOiJIUzI1NiJ9  ") == "eyJhbGciOiJIUzI1NiJ9"

def test_empty_raises():
    with pytest.raises(ValueError):
        normalize_token("")

def test_only_whitespace_raises():
    with pytest.raises(ValueError):
        normalize_token("   ")

def test_bearer_only_raises():
    with pytest.raises(ValueError):
        normalize_token("Bearer ")

def test_token_not_modified_without_prefix():
    t = "some-opaque-token-123"
    assert normalize_token(t) == t
