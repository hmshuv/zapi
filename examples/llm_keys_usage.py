"""
Example demonstrating LLM API key management with ZAPI.

This shows how to securely provide LLM API keys that will be encrypted
and transmitted to the adopt.ai discovery service.
"""

from zapi import ZAPI, LLMProvider


def main():
    # Example 1: Initialize ZAPI with LLM keys in constructor
    print("Example 1: ZAPI with LLM keys in constructor (Anthropic primary support)")
    
    # Generic key-value approach - Anthropic is fully supported
    llm_keys = {
        "anthropic": "sk-ant-your-anthropic-key-here",  # Primary supported provider
        "openai": "sk-your-openai-key-here"             # Extended support
    }
    
    z = ZAPI(
        client_id="YOUR_CLIENT_ID",
        secret="YOUR_SECRET",
        llm_keys=llm_keys
    )
    
    print(f"Configured providers: {z.get_llm_providers()}")
    print(f"Has LLM keys: {z.has_llm_keys()}")
    
    # Launch browser and capture session
    session = z.launch_browser(url="https://app.example.com", headless=False)
    input("Navigate around the app, then press ENTER to continue...")
    
    # Export HAR with encrypted LLM keys
    session.dump_logs("example_with_keys.har")
    
    # Upload to adopt.ai with encrypted keys
    z.upload_har("example_with_keys.har")
    
    session.close()
    print("✓ Session completed with encrypted LLM keys included\n")
    
    
    # Example 2: Set LLM keys after initialization
    print("Example 2: Setting LLM keys after initialization")
    
    z2 = ZAPI(client_id="YOUR_CLIENT_ID", secret="YOUR_SECRET")
    print(f"Initially has keys: {z2.has_llm_keys()}")
    
    # Add keys later - showcasing primary Anthropic support
    z2.set_llm_keys({
        "anthropic": "sk-ant-another-key-here"  # Primary supported provider
    })
    
    print(f"After setting keys: {z2.has_llm_keys()}")
    print(f"Configured providers: {z2.get_llm_providers()}")
    
    
    # Example 3: Working without LLM keys (backward compatibility)
    print("\nExample 3: Working without LLM keys (backward compatibility)")
    
    z3 = ZAPI(client_id="YOUR_CLIENT_ID", secret="YOUR_SECRET")
    print(f"Has LLM keys: {z3.has_llm_keys()}")
    
    # This will work exactly as before - no encrypted keys sent
    session3 = z3.launch_browser(url="https://app.example.com")
    session3.wait_for(timeout=1000)
    session3.dump_logs("example_no_keys.har")
    z3.upload_har("example_no_keys.har")  # byok_enabled: false
    session3.close()
    print("✓ Session completed without LLM keys (legacy mode)")
    
    
    # Example 4: Show supported providers with support levels
    print("\nExample 4: Supported LLM providers (generic key-value approach)")
    print(f"All supported providers: {list(LLMProvider.get_all_providers())}")
    
    from zapi.providers import get_supported_providers_info, is_primary_provider
    
    providers_info = get_supported_providers_info()
    for provider_name, info in providers_info.items():
        support_level = "🔥 PRIMARY" if is_primary_provider(provider_name) else "📦 Extended"
        print(f"- {info['display_name']}: {support_level} - {info['description']}")
    
    print("\n💡 Generic approach: You can use any provider with {\"provider\": \"api_key\"} format!")
    print("   Anthropic gets full validation, others get basic validation for extensibility.")


if __name__ == "__main__":
    main()
