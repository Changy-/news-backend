import os
import sys

# Add the parent directory to sys.path so we can import services
sys.path.append(os.getcwd())

from services import ai_service
from dotenv import load_dotenv

load_dotenv()

def test_provider(provider_name):
    print(f"--- Testing Provider: {provider_name} ---")
    
    # We need to reload the module or re-set the variable because it's read at module level
    # But for this simple script, we can just patch the variable in the module if we were mocking,
    # but since the module reads env var at top level, we might need to use `reload` or just set the internal variable if we changed it.
    # In my implementation: 
    # AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
    # This is at top level. 
    # To test switching, updating os.environ BEFORE import would work, but we already imported.
    # Let's iterate.
    pass

if __name__ == "__main__":
    # Test 1: Check default (Gemini) or what's in env
    print(f"Current Configured Provider: {ai_service.AI_PROVIDER}")
    
    text = "This is a test article content to summarize."
    summary = ai_service.generate_summary(text)
    print(f"Summary result: {summary}")

    # Test 2: Simulate OpenAI missing key
    # We can manually switch the provider variable for testing purposes since it's a global var in the module
    ai_service.AI_PROVIDER = "openai"
    print(f"\nSwitched to OpenAI (simulated)...")
    summary_openai = ai_service.generate_summary(text)
    print(f"Summary result (OpenAI): {summary_openai}")
