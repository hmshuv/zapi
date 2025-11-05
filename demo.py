#!/usr/bin/env python
"""ZAPI Demo Script"""
from zapi import (
    ZAPI, 
    load_llm_credentials,
    ZAPIError,
    ZAPIAuthenticationError,
    ZAPIValidationError,
    ZAPINetworkError,
    BrowserSessionError,
    BrowserNavigationError,
    BrowserInitializationError
)


def main():
    client_id = "CLIENT_ID"
    secret = "SECRET_KEY"
    url = "URL"
    output_file = "OUTPUT_FILE.har"
    
    # Load LLM credentials securely from .env or fallback to code
    print("🔐 Loading LLM credentials...")
    llm_provider, llm_api_key, llm_model_name = load_llm_credentials()
    
    try:
        # Initialize ZAPI with LLM credentials
        print(f"Initializing ZAPI with BYOK - {llm_provider} for enhanced API discovery...")
        z = ZAPI(
            client_id=client_id, 
            secret=secret, 
            llm_provider=llm_provider,
            llm_model_name=llm_model_name,
            llm_api_key=llm_api_key
        )
        print(f"Configured LLM provider: {z.get_llm_provider()}")
        print(f"Configured LLM model name: {z.get_llm_model_name()}")
        
        # Launch browser with enhanced error handling
        print(f"🌐 Launching browser and navigating to: {url}")
        session = z.launch_browser(url=url, headless=False)
        
        print("✅ Browser launched successfully!")
        input("📋 Navigate around the app, then press ENTER when done navigating and want to save the session...")
        
        print("💾 Saving session logs...")
        session.dump_logs(output_file)
        print(f"✅ Session saved to: {output_file}")
        
        print("☁️ Uploading HAR file...")
        z.upload_har(output_file)
        print("✅ HAR file uploaded successfully!")
        
        # print the decrypted LLM key 
        # print(f"Decrypted LLM key: {z.get_decrypted_llm_key()}")
        session.close()
        print("🎉 Demo completed successfully!")
        
    except ZAPIValidationError as e:
        print("❌ Configuration Validation Error:")
        print(f"   {str(e)}")
        print("💡 Please check your input values:")
        print(f"   - URL: '{url}' (should be like 'https://example.com')")
        print(f"   - Output file: '{output_file}' (should end with '.har')")
        print("   Make sure to replace placeholder values with actual ones.")
        return 1
        
    except ZAPIAuthenticationError as e:
        print("❌ Authentication Error:")
        print(f"   {str(e)}")
        print("💡 Please check your credentials:")
        print(f"   - Client ID: {client_id}")
        print("   - Secret: [HIDDEN]")
        print("   - Make sure your account is active and has proper permissions")
        return 1
        
    except ZAPINetworkError as e:
        print("❌ Network Error:")
        print(f"   {str(e)}")
        print("💡 This might be due to:")
        print("   - Internet connectivity issues")
        print("   - ZAPI service being temporarily unavailable")
        print("   - Firewall or proxy blocking the connection")
        print("   - DNS resolution problems")
        return 1
        
    except BrowserNavigationError as e:
        print("❌ Browser Navigation Error:")
        print(f"   {str(e)}")
        print("💡 Common solutions:")
        print(f"   - Check URL format: '{url}'")
        print("   - Ensure the website is accessible")
        print("   - Try a different URL for testing")
        print("   - Check your internet connection")
        return 1
        
    except BrowserInitializationError as e:
        print("❌ Browser Initialization Error:")
        print(f"   {str(e)}")
        print("💡 This might be due to:")
        print("   - Missing browser dependencies (try: playwright install)")
        print("   - System permissions issues")
        print("   - Insufficient system resources")
        return 1
        
    except BrowserSessionError as e:
        print("❌ Browser Session Error:")
        print(f"   {str(e)}")
        print("💡 Try the following:")
        print("   - Restart the script")
        print("   - Check if the browser window is responsive")
        print("   - Ensure sufficient disk space for HAR files")
        return 1
        
    except ZAPIError as e:
        print("❌ ZAPI Error:")
        print(f"   {str(e)}")
        print("💡 This is a general ZAPI error. Please check your configuration.")
        return 1
        
    except Exception as e:
        print("❌ Unexpected Error:")
        print(f"   {str(e)}")
        print("💡 This is an unexpected error. Please:")
        print("   - Check all your input values")
        print("   - Try running the script again")
        print("   - Contact support if the issue persists")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())