#!/usr/bin/env python
"""ZAPI Demo Script - Simplified"""

from zapi import ZAPI
import zapi


def main():
    # Get user input
    use_example = input("Use example values? (y/n): ").lower().strip() == 'y'
    
    if use_example:
        client_id = "453af936-d525-4fe5-9e7f-c7bf434a8387"
        secret = "73f30753-dcf2-4e5e-be7d-9e474a04aca9"
        url = "https://app.adopt.ai"
        output_file = "demo_session.har"
    else:
        client_id = input("Enter your client ID: ").strip()
        secret = input("Enter your secret: ").strip()
        url = input("Enter URL to visit: ").strip()
        output_file = input("Enter output filename (default: session.har): ").strip() or "session.har"
    
    try:
        # Initialize and run ZAPI
        z = ZAPI(client_id=client_id, secret=secret)
        session = z.launch_browser(url=url, headless=False)
        
        input("Press ENTER when done navigating...")
        
        session.dump_logs(output_file)
        zapi.upload_har(output_file)
        session.close()
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

