"""BrowserSession implementation with Playwright integration."""

import asyncio
from pathlib import Path
from typing import Optional, Union
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)

from .auth import get_auth_handler


def _run_async(coro):
    """Helper to run async coroutines synchronously."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # If we're already in an async context, just return the coroutine
        return coro
    else:
        # Run synchronously
        return loop.run_until_complete(coro)


class BrowserSession:
    """
    Manages a Playwright browser session with HAR recording and network log capture.
    
    This class handles browser lifecycle, authentication injection, navigation,
    and HAR file export for API discovery.
    """
    
    def __init__(
        self,
        auth_token: str,
        headless: bool = True,
        **playwright_options
    ):
        """
        Initialize a browser session.
        
        Args:
            auth_token: Authentication token to inject via Authorization header
            headless: Whether to run browser in headless mode
            **playwright_options: Additional options for Playwright browser launch
        """
        self.auth_token = auth_token
        self.headless = headless
        self.playwright_options = playwright_options
        
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._har_path: Optional[Path] = None
        
    async def _initialize(self, initial_url: Optional[str] = None, wait_until: str = "load"):
        """
        Initialize Playwright browser, context, and page.
        
        Args:
            initial_url: Optional initial URL to navigate to
            wait_until: When to consider navigation complete (default: "load")
        """
        # Start Playwright
        self._playwright = await async_playwright().start()
        
        # Launch browser
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            **self.playwright_options
        )
        
        # Create temporary HAR file path
        import tempfile
        self._har_path = Path(tempfile.mktemp(suffix=".har"))
        
        # Create context with HAR recording
        self._context = await self._browser.new_context(
            record_har_path=str(self._har_path),
            record_har_mode="minimal",
        )
        
        # Apply header-based authentication (Bearer token)
        auth_handler = get_auth_handler("header")
        await auth_handler(self._context, self.auth_token)
        
        # Create page
        self._page = await self._context.new_page()
        
        # Navigate to initial URL if provided
        if initial_url:
            await self._navigate_async(initial_url, wait_until=wait_until)
    
    async def _navigate_async(self, url: str, wait_until: str = "load") -> None:
        """
        Internal async navigate method.
        
        Args:
            url: URL to navigate to
            wait_until: When to consider navigation complete
                       ("load", "domcontentloaded", "networkidle")
        """
        if not self._page:
            raise RuntimeError("Browser session not initialized. Call _initialize() first.")
        
        # Navigate with Authorization header already set
        await self._page.goto(url, wait_until=wait_until)
    
    def navigate(self, url: str, wait_until: str = "load") -> None:
        """
        Navigate to a URL with authentication injection.
        
        Args:
            url: URL to navigate to
            wait_until: When to consider navigation complete
                       ("load", "domcontentloaded", "networkidle")
        """
        _run_async(self._navigate_async(url, wait_until))
    
    async def _click_async(self, selector: str, **kwargs) -> None:
        """Internal async click method."""
        if not self._page:
            raise RuntimeError("Browser session not initialized.")
        await self._page.click(selector, **kwargs)
    
    def click(self, selector: str, **kwargs) -> None:
        """
        Click an element by selector.
        
        Args:
            selector: CSS selector for the element
            **kwargs: Additional options for Playwright click
        """
        _run_async(self._click_async(selector, **kwargs))
    
    async def _fill_async(self, selector: str, value: str, **kwargs) -> None:
        """Internal async fill method."""
        if not self._page:
            raise RuntimeError("Browser session not initialized.")
        await self._page.fill(selector, value, **kwargs)
    
    def fill(self, selector: str, value: str, **kwargs) -> None:
        """
        Fill a form field.
        
        Args:
            selector: CSS selector for the input element
            value: Value to fill
            **kwargs: Additional options for Playwright fill
        """
        _run_async(self._fill_async(selector, value, **kwargs))
    
    async def _wait_for_async(
        self, 
        selector: Optional[str] = None, 
        timeout: Optional[float] = None
    ) -> None:
        """Internal async wait_for method."""
        if not self._page:
            raise RuntimeError("Browser session not initialized.")
        
        if selector:
            await self._page.wait_for_selector(selector, timeout=timeout)
        elif timeout:
            await self._page.wait_for_timeout(timeout)
        else:
            raise ValueError("Must provide either selector or timeout")
    
    def wait_for(
        self, 
        selector: Optional[str] = None, 
        timeout: Optional[float] = None
    ) -> None:
        """
        Wait for a selector or timeout.
        
        Args:
            selector: CSS selector to wait for (if None, waits for timeout)
            timeout: Timeout in milliseconds
        """
        _run_async(self._wait_for_async(selector, timeout))
    
    async def _dump_logs_async(self, filepath: Union[str, Path]) -> None:
        """Internal async dump_logs method."""
        if not self._context:
            raise RuntimeError("Browser session not initialized.")
        
        # Close context to finalize HAR recording
        await self._context.close()
        
        # Copy HAR file to destination
        if self._har_path and self._har_path.exists():
            import shutil
            shutil.copy(self._har_path, filepath)
            # Clean up temporary file
            self._har_path.unlink()
        else:
            raise RuntimeError("HAR file not found. Session may not have been properly initialized.")
        
        # Mark context as closed
        self._context = None
        self._page = None
    
    def dump_logs(self, filepath: Union[str, Path]) -> None:
        """
        Export captured network logs to a HAR file.
        
        Args:
            filepath: Path where to save the HAR file
        """
        _run_async(self._dump_logs_async(filepath))
    
    async def _close_async(self) -> None:
        """Internal async close method."""
        if self._context:
            await self._context.close()
        
        if self._browser:
            await self._browser.close()
        
        if self._playwright:
            await self._playwright.stop()
        
        # Clean up temporary HAR file if it exists
        if self._har_path and self._har_path.exists():
            self._har_path.unlink()
        
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
    
    def close(self) -> None:
        """
        Close the browser session and cleanup resources.
        """
        _run_async(self._close_async())
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_async()
        return False

