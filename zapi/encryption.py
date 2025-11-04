"""Secure encryption/decryption utilities for LLM API keys."""

import base64
import json
import secrets
from typing import Dict, Optional, Tuple

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class LLMKeyEncryption:
    """Handles encryption/decryption of LLM API keys using org_id as context."""
    
    # Constants for encryption
    KEY_LENGTH = 32  # 256 bits for AES-256
    NONCE_LENGTH = 12  # 96 bits for GCM
    SALT_LENGTH = 16  # 128 bits
    TAG_LENGTH = 16  # 128 bits for GCM tag
    ITERATIONS = 100000  # PBKDF2 iterations
    
    def __init__(self, org_id: str):
        """
        Initialize encryption handler with organization ID.
        
        Args:
            org_id: Organization ID used as encryption context
            
        Raises:
            ValueError: If org_id is empty or invalid
        """
        if not org_id or not org_id.strip():
            raise ValueError("org_id cannot be empty")
        
        self.org_id = org_id.strip()
    
    def _derive_key(self, salt: bytes) -> bytes:
        """
        Derive encryption key from org_id using PBKDF2.
        
        Args:
            salt: Random salt for key derivation
            
        Returns:
            Derived encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_LENGTH,
            salt=salt,
            iterations=self.ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(self.org_id.encode('utf-8'))
    
    def encrypt_keys(self, llm_keys: Dict[str, str]) -> str:
        """
        Encrypt LLM API keys dictionary.
        
        Args:
            llm_keys: Dictionary mapping provider names to API keys
            
        Returns:
            Base64-encoded encrypted data with embedded salt and nonce
            
        Raises:
            ValueError: If encryption fails
        """
        if not llm_keys:
            raise ValueError("llm_keys cannot be empty")
        
        try:
            # Generate random salt and nonce
            salt = secrets.token_bytes(self.SALT_LENGTH)
            nonce = secrets.token_bytes(self.NONCE_LENGTH)
            
            # Derive encryption key
            key = self._derive_key(salt)
            
            # Serialize keys to JSON
            plaintext = json.dumps(llm_keys, separators=(',', ':')).encode('utf-8')
            
            # Encrypt using AES-256-GCM
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(plaintext) + encryptor.finalize()
            
            # Package: salt + nonce + ciphertext + tag
            encrypted_data = salt + nonce + ciphertext + encryptor.tag
            
            # Return base64-encoded result
            return base64.b64encode(encrypted_data).decode('ascii')
            
        except Exception as e:
            raise ValueError(f"Failed to encrypt LLM keys: {e}")
        finally:
            # Clear sensitive data from memory
            if 'key' in locals():
                key = b'\x00' * len(key)
            if 'plaintext' in locals():
                plaintext = b'\x00' * len(plaintext)
    
    def decrypt_keys(self, encrypted_data: str) -> Dict[str, str]:
        """
        Decrypt LLM API keys from encrypted data.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Dictionary mapping provider names to API keys
            
        Raises:
            ValueError: If decryption fails or data is corrupted
        """
        if not encrypted_data or not encrypted_data.strip():
            raise ValueError("encrypted_data cannot be empty")
        
        key = None
        plaintext = None
        
        try:
            # Decode base64 data
            try:
                data = base64.b64decode(encrypted_data.encode('ascii'))
            except Exception as e:
                raise ValueError(f"Invalid base64 encoding: {e}")
            
            # Validate minimum length
            min_length = self.SALT_LENGTH + self.NONCE_LENGTH + self.TAG_LENGTH + 1
            if len(data) < min_length:
                raise ValueError("Encrypted data is too short")
            
            # Extract components
            salt = data[:self.SALT_LENGTH]
            nonce = data[self.SALT_LENGTH:self.SALT_LENGTH + self.NONCE_LENGTH]
            tag_start = len(data) - self.TAG_LENGTH
            ciphertext = data[self.SALT_LENGTH + self.NONCE_LENGTH:tag_start]
            tag = data[tag_start:]
            
            # Derive decryption key
            key = self._derive_key(salt)
            
            # Decrypt using AES-256-GCM
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Parse JSON
            try:
                llm_keys = json.loads(plaintext.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise ValueError(f"Failed to parse decrypted data: {e}")
            
            if not isinstance(llm_keys, dict):
                raise ValueError("Decrypted data is not a valid key dictionary")
            
            return llm_keys
            
        except Exception as e:
            if "Failed to parse decrypted data" in str(e) or "Invalid base64" in str(e):
                raise
            raise ValueError(f"Failed to decrypt LLM keys: {e}")
        finally:
            # Clear sensitive data from memory
            if key is not None:
                key = b'\x00' * len(key)
            if plaintext is not None:
                plaintext = b'\x00' * len(plaintext)


def encrypt_llm_keys(org_id: str, llm_keys: Dict[str, str]) -> str:
    """
    Convenience function to encrypt LLM keys.
    
    Args:
        org_id: Organization ID for encryption context
        llm_keys: Dictionary of provider names to API keys
        
    Returns:
        Base64-encoded encrypted data
    """
    encryptor = LLMKeyEncryption(org_id)
    return encryptor.encrypt_keys(llm_keys)


def decrypt_llm_keys(org_id: str, encrypted_data: str) -> Dict[str, str]:
    """
    Convenience function to decrypt LLM keys.
    
    Args:
        org_id: Organization ID for decryption context
        encrypted_data: Base64-encoded encrypted data
        
    Returns:
        Dictionary of provider names to API keys
    """
    decryptor = LLMKeyEncryption(org_id)
    return decryptor.decrypt_keys(encrypted_data)


def secure_compare_keys(keys1: Optional[Dict[str, str]], keys2: Optional[Dict[str, str]]) -> bool:
    """
    Securely compare two key dictionaries without timing attacks.
    
    Args:
        keys1: First key dictionary
        keys2: Second key dictionary
        
    Returns:
        True if dictionaries are equal, False otherwise
    """
    if keys1 is None and keys2 is None:
        return True
    if keys1 is None or keys2 is None:
        return False
    
    if len(keys1) != len(keys2):
        return False
    
    # Compare each key-value pair securely
    result = True
    for provider in set(keys1.keys()) | set(keys2.keys()):
        key1 = keys1.get(provider, "")
        key2 = keys2.get(provider, "")
        
        # Use secrets.compare_digest for timing-safe comparison
        if not secrets.compare_digest(key1, key2):
            result = False
    
    return result
