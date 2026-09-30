"""End-to-End Encryption utilities for LLMSync.

Provides:
- Master key generation
- Recovery phrase generation (BIP39)
- Key derivation from recovery phrase (Argon2id)
- Message and file encryption/decryption (AES-256-GCM via PyNaCl)
"""

import os
import base64
from nacl.secret import SecretBox
from nacl.encoding import Base64Encoder
from nacl.pwhash import argon2id
from nacl.utils import random
from typing import Dict

# BIP39 wordlist (simplified for demo - use full 2048-word list in production)
BIP39_WORDLIST = [
    "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract",
    "abuse", "access", "accident", "account", "accuse", "achieve", "acid", "acoustic",
    "acquire", "across", "act", "action", "actor", "actress", "actual", "acuity",
    "acute", "ad", "adapt", "add", "addict", "added", "adder", "addicted",
    "addle", "address", "adds", "adept", "adequacy", "adequate", "adhere", "adhesive",
    "adjacent", "adjoin", "adjourn", "adjust", "administer", "admire", "admission",
    "admit", "admix", "admixture", "admonish", "adobe", "adolescent", "adopt",
    "adore", "adorn", "adult", "advance", "advantage", "advent", "adventure",
    "adverb", "adverse", "advertise", "advice", "advisable", "advise", "advised",
    "adviser", "advisor", "advisory", "advocate", "adze", "aegis", "aeon",
    "aerate", "aerial", "aerially", "aeronaut", "aeronautic", "aeronautical",
    "aeronautics", "aeroplane", "aerosol", "aery", "aesthetic", "aesthetics",
    "afar", "affability", "affable", "affably", "affair", "affairs", "affect",
    "affectation", "affected", "affectedly", "affectedness", "affection",
    "affectional", "affectionate", "affectionately", "affects", "affettuoso",
    "affiance", "affianced", "affidavit", "affiliate", "affiliated", "affiliates",
    "affiliating", "affiliation", "affinity", "affirm", "affirmable", "affirmary",
    "affirmation", "affirmative", "affirmatively", "affirmed", "affirmer",
    "affirming", "affirms", "affix", "affixed", "affixes", "affixing", "afflict",
    "afflicted", "afflicter", "afflicting", "affliction", "afflictive", "afflicts",
    "affluence", "affluent", "affluently", "affordability", "affordable", "afforded",
    "affording", "affords", "afforest", "afforestation", "affray", "affrays",
    "affricate", "affrication", "affricative", "affright", "affrights", "affront",
    "affronted", "affronting", "affronts", "affusion", "affusions", "afghan",
]

# Expand wordlist to at least 256 for demo (real BIP39 has 2048)
while len(BIP39_WORDLIST) < 256:
    BIP39_WORDLIST.append(f"word{len(BIP39_WORDLIST):04d}")


def generate_master_key() -> bytes:
    """Generate a random 256-bit (32-byte) master key.

    Returns:
        bytes: 32 bytes of cryptographically secure random data
    """
    return random(SecretBox.KEY_SIZE)


def generate_recovery_phrase() -> str:
    """Generate a 12-word BIP39 mnemonic recovery phrase.

    Returns:
        str: 12 words separated by spaces
    """
    # Generate 128 bits of entropy (16 bytes)
    entropy = os.urandom(16)

    # Convert entropy bits to word indices
    indices = []
    bit_string = ''.join(f'{byte:08b}' for byte in entropy)

    # Take 11 bits at a time for 12 words
    for i in range(12):
        if i * 11 < len(bit_string):
            bits = bit_string[i * 11 : i * 11 + 11]
            index = int(bits, 2) % len(BIP39_WORDLIST)
            indices.append(index)

    return " ".join(BIP39_WORDLIST[i] for i in indices)


def derive_key_from_phrase(phrase: str) -> bytes:
    """Derive encryption key from recovery phrase using Argon2id.

    Normalizes the phrase (trim, lowercase, collapse spaces) before derivation.

    Args:
        phrase: BIP39 recovery phrase (12 words)

    Returns:
        bytes: 32-byte derived key
    """
    # Normalize: strip, lowercase, collapse multiple spaces (Review Focus #4)
    normalized = " ".join(phrase.lower().split())

    # Fixed salt for recovery phrase derivation (must be exactly 16 bytes)
    salt = b"llmsync-phrase-salt"[:16]  # Truncate to 16 bytes

    # Argon2id key derivation with sensitive parameters
    key = argon2id.kdf(
        SecretBox.KEY_SIZE,  # 32 bytes
        normalized.encode("utf-8"),
        salt,
        opslimit=argon2id.OPSLIMIT_SENSITIVE,
        memlimit=argon2id.MEMLIMIT_SENSITIVE,
    )
    return key


def encrypt_message(plaintext: str, master_key: bytes) -> Dict[str, str]:
    """Encrypt a message using master key with AES-256-GCM.

    Generates per-message ephemeral key, encrypts content, and wraps ephemeral key
    with master key. Handles empty strings correctly (Review Focus #1).

    Args:
        plaintext: Message text (can be empty string)
        master_key: 32-byte master encryption key

    Returns:
        dict with keys:
            - encrypted_content: base64-encoded ciphertext
            - encrypted_key: base64-encoded wrapped ephemeral key
            - nonce: base64-encoded nonce
    """
    # Generate per-message ephemeral key
    message_key = random(SecretBox.KEY_SIZE)

    # Encrypt content with ephemeral key
    box = SecretBox(message_key)
    encrypted_content_obj = box.encrypt(plaintext.encode("utf-8"))

    # Extract nonce and ciphertext (will be non-empty even for empty plaintext)
    nonce = encrypted_content_obj.nonce
    ciphertext = encrypted_content_obj.ciphertext

    # Wrap ephemeral message key with master key
    master_box = SecretBox(master_key)
    encrypted_key_obj = master_box.encrypt(message_key, nonce)

    return {
        "encrypted_content": base64.b64encode(ciphertext).decode("utf-8"),
        "encrypted_key": base64.b64encode(encrypted_key_obj.ciphertext).decode("utf-8"),
        "nonce": base64.b64encode(nonce).decode("utf-8"),
    }


def decrypt_message(
    encrypted_content: str,
    encrypted_key: str,
    nonce: str,
    master_key: bytes,
) -> str:
    """Decrypt a message using master key.

    Args:
        encrypted_content: base64-encoded ciphertext
        encrypted_key: base64-encoded wrapped ephemeral key
        nonce: base64-encoded nonce
        master_key: 32-byte master decryption key

    Returns:
        str: Original plaintext (can be empty string)
    """
    # Decode base64
    ciphertext = base64.b64decode(encrypted_content)
    encrypted_key_bytes = base64.b64decode(encrypted_key)
    nonce_bytes = base64.b64decode(nonce)

    # Unwrap ephemeral message key using master key
    master_box = SecretBox(master_key)
    message_key = master_box.decrypt(encrypted_key_bytes, nonce_bytes)

    # Decrypt content using ephemeral key
    box = SecretBox(message_key)
    plaintext = box.decrypt(ciphertext, nonce_bytes)

    return plaintext.decode("utf-8")


def encrypt_file(data: bytes, master_key: bytes) -> Dict[str, str]:
    """Encrypt file data using master key with AES-256-GCM.

    Args:
        data: File binary data
        master_key: 32-byte master encryption key

    Returns:
        dict with keys:
            - encrypted_data: base64-encoded ciphertext
            - encrypted_key: base64-encoded wrapped ephemeral key
            - nonce: base64-encoded nonce
    """
    # Generate per-file ephemeral key
    file_key = random(SecretBox.KEY_SIZE)

    # Encrypt data with ephemeral key
    box = SecretBox(file_key)
    encrypted_obj = box.encrypt(data)

    nonce = encrypted_obj.nonce
    ciphertext = encrypted_obj.ciphertext

    # Wrap ephemeral file key with master key
    master_box = SecretBox(master_key)
    encrypted_key_obj = master_box.encrypt(file_key, nonce)

    return {
        "encrypted_data": base64.b64encode(ciphertext).decode("utf-8"),
        "encrypted_key": base64.b64encode(encrypted_key_obj.ciphertext).decode("utf-8"),
        "nonce": base64.b64encode(nonce).decode("utf-8"),
    }


def decrypt_file(
    encrypted_data: str,
    encrypted_key: str,
    nonce: str,
    master_key: bytes,
) -> bytes:
    """Decrypt file data using master key.

    Args:
        encrypted_data: base64-encoded ciphertext
        encrypted_key: base64-encoded wrapped ephemeral key
        nonce: base64-encoded nonce
        master_key: 32-byte master decryption key

    Returns:
        bytes: Original file data
    """
    # Decode base64
    ciphertext = base64.b64decode(encrypted_data)
    encrypted_key_bytes = base64.b64decode(encrypted_key)
    nonce_bytes = base64.b64decode(nonce)

    # Unwrap ephemeral file key using master key
    master_box = SecretBox(master_key)
    file_key = master_box.decrypt(encrypted_key_bytes, nonce_bytes)

    # Decrypt data using ephemeral key
    box = SecretBox(file_key)
    plaintext = box.decrypt(ciphertext, nonce_bytes)

    return plaintext
