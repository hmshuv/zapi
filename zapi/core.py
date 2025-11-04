"""Core ZAPI class implementation."""

import asyncio
import json
import requests
import httpx
from typing import Optional, Dict
from .session import BrowserSession
from .providers import validate_llm_keys
from .encryption import LLMKeyEncryption


class ZAPI:
    """
    Zero-Config API Intelligence main class.
    
    This class provides a simple interface to launch browser sessions,
    capture network traffic, and export HAR files for API discovery.
    """
    
    def __init__(
        self, 
        client_id: str,
        secret: str,
        llm_keys: Optional[Dict[str, str]] = None
    ):
        """
        Initialize ZAPI instance.
        
        Args:
            client_id: Client ID for authentication
            secret: Secret key for authentication
            llm_keys: Optional dictionary of LLM provider API keys
                     Format: {"provider": "api_key"} (e.g., {"anthropic": "sk-ant-..."})
            
        Raises:
            ValueError: If client_id or secret is empty, or llm_keys format is invalid
            RuntimeError: If token fetch fails
        """
        if not client_id or not client_id.strip():
            raise ValueError("client_id cannot be empty")
        if not secret or not secret.strip():
            raise ValueError("secret cannot be empty")
        
        self.client_id = client_id
        self.secret = secret
        
        # Fetch auth token and extract org_id
        self.auth_token, self.org_id = self._fetch_auth_token()
        
        # Initialize encryption handler
        self._key_encryptor = LLMKeyEncryption(self.org_id)
        
        # Validate and encrypt LLM keys if provided
        self._encrypted_llm_keys: Optional[str] = None
        if llm_keys:
            self.set_llm_keys(llm_keys)
    
    def _fetch_auth_token(self) -> tuple[str, str]:
        """
        Fetch authentication token from adopt.ai API and extract org_id.
        
        Returns:
            Tuple of (authentication_token, org_id)
            
        Raises:
            RuntimeError: If token fetch fails or org_id extraction fails
        """
        url = "https://connect.adopt.ai/v1/auth/token"
        payload = {
            "clientId": self.client_id,
            "secret": self.secret
        }
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract token from response
            if "token" in data:
                token = data["token"]
            elif "access_token" in data:
                token = data["access_token"]
            else:
                raise RuntimeError(f"Unexpected response format: {data}")
            
            # Validate token and extract org_id via backend API
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            org_id = loop.run_until_complete(self._validate_token_and_extract_org_id(token))
            
            return token, org_id
                
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch authentication token: {e}")
    
    async def _validate_token_and_extract_org_id(self, token: str) -> str:
        """
        Validate JWT token via backend API and extract org_id.
        
        Args:
            token: JWT token string
            
        Returns:
            Organization ID extracted from validated token
            
        Raises:
            RuntimeError: If token validation fails or org_id extraction fails
        """
        # Use adopt.ai backend API for token validation
        backend_url = "https://api.adopt.ai"  # Adjust if different
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{backend_url}/v1/users/validate-token",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                
                validation_result = response.json()
                
                if not validation_result.get('valid'):
                    raise RuntimeError("Token validation failed")
                
                org_id = validation_result.get('org_id')
                if not org_id or not isinstance(org_id, str):
                    raise RuntimeError("Invalid org_id in validation response")

                print(f"Org ID: {org_id}")
                
                return org_id
                
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Backend token validation failed: HTTP {e.response.status_code}")
            except httpx.RequestError as e:
                raise RuntimeError(f"Token validation request failed: {e}")
            except Exception as e:
                raise RuntimeError(f"Token validation error: {e}")
    
    def set_llm_keys(self, llm_keys: Dict[str, str]) -> None:
        """
        Set LLM API keys for the session.
        
        Args:
            llm_keys: Dictionary mapping provider names to API keys
                     Format: {"provider": "api_key"} (e.g., {"anthropic": "sk-ant-..."})
            
        Raises:
            ValueError: If llm_keys format is invalid
            RuntimeError: If encryption fails
        """
        if not llm_keys:
            self._encrypted_llm_keys = None
            return
        
        # Validate keys format and providers
        validated_keys = validate_llm_keys(llm_keys)
        
        # Encrypt the keys using org_id
        try:
            self._encrypted_llm_keys = self._key_encryptor.encrypt_keys(validated_keys)
        except Exception as e:
            raise RuntimeError(f"Failed to encrypt LLM keys: {e}")
    
    def get_llm_providers(self) -> list[str]:
        """
        Get list of configured LLM providers.
        
        Returns:
            List of provider names that have been configured
        """
        if not self._encrypted_llm_keys:
            return []
        
        try:
            decrypted_keys = self._key_encryptor.decrypt_keys(self._encrypted_llm_keys)
            return list(decrypted_keys.keys())
        except Exception:
            return []
    
    def has_llm_keys(self) -> bool:
        """
        Check if LLM keys are configured.
        
        Returns:
            True if LLM keys are set, False otherwise
        """
        return self._encrypted_llm_keys is not None
    
    def launch_browser(
        self,
        url: str,
        headless: bool = True,
        wait_until: str = "load",
        **playwright_options
    ) -> BrowserSession:
        """
        Launch a browser session with network logging.
        
        Args:
            url: Initial URL to navigate to
            headless: Whether to run browser in headless mode (default: True)
            wait_until: When to consider navigation complete (default: "load")
                       Options: "load", "domcontentloaded", "networkidle"
            **playwright_options: Additional Playwright browser launch options
            
        Returns:
            BrowserSession instance ready for navigation and interaction
            
        Example:
            >>> z = ZAPI(client_id="YOUR_CLIENT_ID", secret="YOUR_SECRET")
            >>> session = z.launch_browser(url="https://app.example.com")
            >>> session.dump_logs("session.har")
            >>> session.close()
        """
        print(f"Launching browser with auth token: {self.auth_token}")
        session = BrowserSession(
            auth_token=self.auth_token,
            headless=headless,
            **playwright_options
        )
        
        # Initialize the session synchronously
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(session._initialize(initial_url=url, wait_until=wait_until))
        
        return session

    def upload_har(self, har_file: str):
        """
        Upload a HAR file to the ZAPI API with optional encrypted LLM keys.
        
        Args:
            har_file: Path to the HAR file to upload
        
        Returns:
            Response JSON from the API
        
        Raises:
            requests.exceptions.RequestException: If the upload fails
        """
        url = "https://api.adopt.ai/v1/api-discovery/upload-file"
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }
        
        # Prepare metadata if LLM keys are configured
        metadata = {}
        if self.has_llm_keys():
            metadata = {
                "encrypted_llm_keys": self._encrypted_llm_keys,
                "byok_enabled": True
            }
        else:
            metadata = {
                "byok_enabled": False
            }
        
        # Prepare multipart form data
        with open(har_file, 'rb') as f:
            files = {
                'file': (har_file, f, 'application/json')
            }
            
            # Add metadata as form data
            data = {
                'metadata': json.dumps(metadata)
            }
            
            response = requests.post(url, headers=headers, files=files, data=data)
        
        print("file uploaded successfully")
        if self.has_llm_keys():
            providers = ", ".join(self.get_llm_providers())
            print(f"Included encrypted keys for providers: {providers}")
        
        response.raise_for_status()
        return response.json()

