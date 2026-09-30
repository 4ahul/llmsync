"""
LLMSync Python SDK

E2E encrypted conversation sync client library.
"""

from .client import LLMSyncClient
from .models import Thread, Message, Device
from .exceptions import LLMSyncError, AuthenticationError, EncryptionError

__version__ = "0.1.0"

__all__ = [
    "LLMSyncClient",
    "Thread",
    "Message",
    "Device",
    "LLMSyncError",
    "AuthenticationError",
    "EncryptionError",
]
