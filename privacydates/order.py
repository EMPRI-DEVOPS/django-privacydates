"""Utilities for ordering contexts"""
from hashlib import sha256


def hash_context_key(key: str) -> str:
    """Return a 64 character hashed context key using SHA256"""
    return sha256(str(key).encode()).hexdigest()
