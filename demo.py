#!/usr/bin/env python
"""ZAPI Demo Script - Simplified"""

from zapi import ZAPI


def main():
    client_id = "client_id"
    secret = "secret"
    url = "https://app.adopt.ai"
    output_file = "demo_session.har"
    
    # Optional: Add your LLM API keys for enhanced API discovery
    # Uncomment and replace with your actual keys
    llm_keys = {
        # "anthropic": "sk-ant-your-key-here",
        # "openai": "sk-your-key-here"
    }
    
    try:
        # Initialize ZAPI with optional LLM keys for enhanced discovery
        if any(llm_keys.values()):
            print("Initializing ZAPI with LLM keys for enhanced API discovery...")
            z = ZAPI(client_id=client_id, secret=secret, llm_keys=llm_keys)
            print(f"Configured LLM providers: {z.get_llm_providers()}")
        else:
            print("Initializing ZAPI without LLM keys...")
            z = ZAPI(client_id=client_id, secret=secret)
        
        session = z.launch_browser(url=url, headless=False)
        input("Press ENTER when done navigating...")
        session.dump_logs(output_file)
        z.upload_har(output_file)
        session.close()
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

