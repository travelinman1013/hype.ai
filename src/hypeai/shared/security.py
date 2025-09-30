"""
Security Utilities.

Token encryption/decryption and other security-related functions.
"""

from config import settings
from cryptography.fernet import Fernet


class TokenEncryption:
    """Utility class for encrypting and decrypting OAuth tokens."""

    @staticmethod
    def _get_cipher() -> Fernet:
        """
        Get Fernet cipher instance.

        Returns:
            Fernet cipher

        Raises:
            ValueError: If encryption key is not set
        """
        if not settings.encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable is not set")

        return Fernet(settings.encryption_key.encode())

    @staticmethod
    def encrypt_token(token: str) -> bytes:
        """
        Encrypt a token string.

        Args:
            token: Token string to encrypt

        Returns:
            Encrypted token as bytes

        Raises:
            ValueError: If encryption key is not set
        """
        cipher = TokenEncryption._get_cipher()
        return cipher.encrypt(token.encode())

    @staticmethod
    def decrypt_token(encrypted_token: bytes) -> str:
        """
        Decrypt an encrypted token.

        Args:
            encrypted_token: Encrypted token bytes

        Returns:
            Decrypted token string

        Raises:
            ValueError: If encryption key is not set or decryption fails
        """
        cipher = TokenEncryption._get_cipher()
        return cipher.decrypt(encrypted_token).decode()


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        Base64-encoded encryption key

    Example:
        >>> key = generate_encryption_key()
        >>> print(f"ENCRYPTION_KEY={key}")
    """
    return Fernet.generate_key().decode()
