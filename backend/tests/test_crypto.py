import pytest
from llmsync.crypto import (
    generate_master_key,
    generate_recovery_phrase,
    derive_key_from_phrase,
    encrypt_message,
    decrypt_message,
    encrypt_file,
    decrypt_file,
)


def test_generate_master_key():
    """Test master key generation produces 32 bytes."""
    key = generate_master_key()
    assert isinstance(key, bytes)
    assert len(key) == 32  # 256 bits


def test_master_key_randomness():
    """Test that master keys are different each time."""
    key1 = generate_master_key()
    key2 = generate_master_key()
    assert key1 != key2


def test_generate_recovery_phrase():
    """Test recovery phrase generation."""
    phrase = generate_recovery_phrase()
    assert isinstance(phrase, str)
    words = phrase.split()
    assert len(words) == 12


def test_recovery_phrase_randomness():
    """Test that recovery phrases are different each time."""
    phrase1 = generate_recovery_phrase()
    phrase2 = generate_recovery_phrase()
    assert phrase1 != phrase2


def test_derive_key_from_phrase():
    """Test key derivation from recovery phrase."""
    phrase = generate_recovery_phrase()
    key = derive_key_from_phrase(phrase)
    assert isinstance(key, bytes)
    assert len(key) == 32  # 256 bits


def test_recovery_phrase_normalization():
    """Test phrase normalization with whitespace (Review Focus #4).

    Recovery phrase with extra whitespace should normalize to same key.
    """
    phrase = generate_recovery_phrase()

    # Derive key from original phrase
    key1 = derive_key_from_phrase(phrase)

    # Add extra whitespace
    phrase_with_whitespace = f"  {phrase.replace(' ', '  ')}  "

    # Derive key from phrase with whitespace
    key2 = derive_key_from_phrase(phrase_with_whitespace)

    # Keys should be identical (normalization works)
    assert key1 == key2


def test_encrypt_decrypt_empty_string():
    """Test empty string encryption/decryption (Review Focus #1).

    Empty message should encrypt and decrypt correctly without crashing.
    """
    master_key = generate_master_key()
    plaintext = ""

    encrypted = encrypt_message(plaintext, master_key)
    assert "encrypted_content" in encrypted
    assert "encrypted_key" in encrypted
    assert "nonce" in encrypted

    # Ciphertext should be non-empty (contains encrypted empty string)
    assert encrypted["encrypted_content"] != ""
    assert encrypted["encrypted_key"] != ""
    assert encrypted["nonce"] != ""

    # Decrypt should return empty string, not None or crash
    decrypted = decrypt_message(
        encrypted["encrypted_content"],
        encrypted["encrypted_key"],
        encrypted["nonce"],
        master_key,
    )
    assert decrypted == ""


def test_encrypt_decrypt_message():
    """Test message encryption and decryption."""
    master_key = generate_master_key()
    plaintext = "Hello, World!"

    encrypted = encrypt_message(plaintext, master_key)
    decrypted = decrypt_message(
        encrypted["encrypted_content"],
        encrypted["encrypted_key"],
        encrypted["nonce"],
        master_key,
    )
    assert decrypted == plaintext


def test_encrypt_decrypt_unicode_message():
    """Test Unicode message encryption and decryption."""
    master_key = generate_master_key()
    plaintext = "こんにちは世界 🌍 مرحبا"

    encrypted = encrypt_message(plaintext, master_key)
    decrypted = decrypt_message(
        encrypted["encrypted_content"],
        encrypted["encrypted_key"],
        encrypted["nonce"],
        master_key,
    )
    assert decrypted == plaintext


def test_encrypt_decrypt_long_message():
    """Test long message encryption and decryption."""
    master_key = generate_master_key()
    plaintext = "A" * 100000  # 100KB

    encrypted = encrypt_message(plaintext, master_key)
    decrypted = decrypt_message(
        encrypted["encrypted_content"],
        encrypted["encrypted_key"],
        encrypted["nonce"],
        master_key,
    )
    assert decrypted == plaintext


def test_decrypt_with_wrong_key_fails():
    """Test that decryption with wrong key fails."""
    key1 = generate_master_key()
    key2 = generate_master_key()
    plaintext = "Secret message"

    encrypted = encrypt_message(plaintext, key1)

    # Decryption with wrong key should raise exception
    with pytest.raises(Exception):  # nacl raises nacl.exceptions.CryptoError
        decrypt_message(
            encrypted["encrypted_content"],
            encrypted["encrypted_key"],
            encrypted["nonce"],
            key2,
        )


def test_encrypt_decrypt_file_empty():
    """Test empty file encryption/decryption."""
    master_key = generate_master_key()
    data = b""

    encrypted = encrypt_file(data, master_key)
    assert "encrypted_data" in encrypted
    assert "encrypted_key" in encrypted
    assert "nonce" in encrypted

    decrypted = decrypt_file(
        encrypted["encrypted_data"],
        encrypted["encrypted_key"],
        encrypted["nonce"],
        master_key,
    )
    assert decrypted == b""


def test_encrypt_decrypt_file():
    """Test file encryption and decryption."""
    master_key = generate_master_key()
    data = b"File contents\x00\x01\x02\x03"

    encrypted = encrypt_file(data, master_key)
    decrypted = decrypt_file(
        encrypted["encrypted_data"],
        encrypted["encrypted_key"],
        encrypted["nonce"],
        master_key,
    )
    assert decrypted == data


def test_encrypt_decrypt_large_file():
    """Test large file encryption and decryption."""
    master_key = generate_master_key()
    data = os.urandom(1000000)  # 1MB random data

    encrypted = encrypt_file(data, master_key)
    decrypted = decrypt_file(
        encrypted["encrypted_data"],
        encrypted["encrypted_key"],
        encrypted["nonce"],
        master_key,
    )
    assert decrypted == data


def test_different_keys_produce_different_ciphertexts():
    """Test that same plaintext with different keys produces different ciphertexts."""
    key1 = generate_master_key()
    key2 = generate_master_key()
    plaintext = "Same message"

    encrypted1 = encrypt_message(plaintext, key1)
    encrypted2 = encrypt_message(plaintext, key2)

    # Ciphertexts should be different
    assert encrypted1["encrypted_content"] != encrypted2["encrypted_content"]


def test_same_message_produces_different_ciphertexts():
    """Test that encrypting same message twice produces different ciphertexts.

    Due to random nonce and ephemeral key generation.
    """
    master_key = generate_master_key()
    plaintext = "Message"

    encrypted1 = encrypt_message(plaintext, master_key)
    encrypted2 = encrypt_message(plaintext, master_key)

    # Ciphertexts should be different (different nonces and ephemeral keys)
    assert encrypted1["encrypted_content"] != encrypted2["encrypted_content"]
    assert encrypted1["nonce"] != encrypted2["nonce"]


import os
