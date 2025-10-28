# ZAPI - Zero-Shot API Discovery

ZAPI is an open-source Python library that automatically captures network traffic and API calls from web applications. Perfect for API discovery, LLM training datasets, and understanding how web apps communicate with backends.


## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install browser binaries (REQUIRED)
playwright install
```

**Requirements:** Python 3.9+, Playwright 1.40.0+

## Quick Start

```python
from zapi import ZAPI

# Initialize with client credentials
z = ZAPI(client_id="YOUR_CLIENT_ID", secret="YOUR_SECRET")

# Launch browser and capture traffic
session = z.launch_browser(url="https://app.example.com/dashboard")

# Export network logs
session.dump_logs("session.har")
session.close()
```

**Test Installation:**
```bash
python demo.py
```

## Usage Examples

### Navigation & Interaction

```python
from zapi import ZAPI

z = ZAPI(client_id="YOUR_CLIENT_ID", secret="YOUR_SECRET")
session = z.launch_browser(url="https://app.example.com")

# Navigate and interact
session.navigate("/dashboard")
session.click("#settings-button")
session.fill("#search-input", "query")
session.wait_for("#results")

session.dump_logs("session.har")
session.close()
```

### Context Manager

```python
z = ZAPI(client_id="YOUR_CLIENT_ID", secret="YOUR_SECRET")

with z.launch_browser(url="https://app.example.com") as session:
    session.navigate("/api-endpoint")
    session.wait_for(timeout=2000)
    session.dump_logs("session.har")
# Auto cleanup
```

### Visible Browser Mode

```python
# Run with visible browser for debugging
session = z.launch_browser(url="https://app.example.com", headless=False)
```

## API Reference

### ZAPI Class

**`ZAPI(client_id, secret)`**
- `client_id` (str): Client ID for OAuth authentication
- `secret` (str): Secret key for authentication

**`launch_browser(url, headless=True, **playwright_options)`**
- Returns: `BrowserSession` instance
- Automatically fetches auth token and injects it into all requests

### BrowserSession Class

| Method | Description |
|--------|-------------|
| `navigate(url, wait_until="networkidle")` | Navigate to URL |
| `click(selector, **kwargs)` | Click element by CSS selector |
| `fill(selector, value, **kwargs)` | Fill form field |
| `wait_for(selector=None, timeout=None)` | Wait for selector or timeout |
| `dump_logs(filepath)` | Export HAR file |
| `close()` | Close browser and cleanup |

## How It Works

When initialized, ZAPI:
1. Calls the adopt.ai OAuth API to obtain an access token
2. Injects the token as a Bearer token in all request headers
3. Captures complete network traffic during browser interactions
4. Exports to standard HAR format compatible with Chrome DevTools
