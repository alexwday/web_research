#!/usr/bin/env python3
"""
Complete Cohere Model Test
Replicates the iris-project authentication flow:
1. Setup SSL certificate
2. OAuth authentication to get token
3. Use OpenAI client to call cohere model at base URL
4. Test streaming and tool calling
"""

import os
import requests
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration - UPDATE THESE WITH YOUR VALUES
CONFIG = {
    # SSL Certificate
    "SSL_CERT_FILENAME": "rbc-ca-bundle.cer",
    
    # OAuth Configuration
    "OAUTH_URL": "https://your-oauth-endpoint.com/oauth/token",  # UPDATE THIS
    "OAUTH_CLIENT_ID": "your-client-id",  # UPDATE THIS
    "OAUTH_CLIENT_SECRET": "your-client-secret",  # UPDATE THIS
    
    # API Configuration  
    "BASE_URL": "https://your-api-endpoint.com/v1",  # UPDATE THIS
    
    # Request Configuration
    "REQUEST_TIMEOUT": 180,
    "MAX_RETRY_ATTEMPTS": 3,
    "RETRY_DELAY_SECONDS": 2,
    "TOKEN_PREVIEW_LENGTH": 7,
    
    # Model Configuration
    "MODEL_SMALL": "gpt-4o-mini-2024-07-18",
    "MODEL_LARGE": "gpt-4o-2024-05-13",
}

def setup_ssl() -> Optional[str]:
    """Setup SSL certificate like iris-project does."""
    script_dir = Path(__file__).parent
    cert_path = script_dir / "ssl_certs" / CONFIG["SSL_CERT_FILENAME"]
    
    if cert_path.exists():
        logger.info(f"Found SSL certificate: {cert_path}")
        # Set environment variables like iris-project
        os.environ["SSL_CERT_FILE"] = str(cert_path)
        os.environ["REQUESTS_CA_BUNDLE"] = str(cert_path)
        logger.info("SSL environment configured successfully")
        return str(cert_path)
    else:
        logger.warning(f"SSL certificate not found at {cert_path}")
        logger.warning("Proceeding without custom SSL certificate")
        return None

def setup_oauth() -> str:
    """Get OAuth token using client credentials flow like iris-project."""
    logger.info("Starting OAuth authentication...")
    
    # Validate settings
    if not all([CONFIG["OAUTH_URL"], CONFIG["OAUTH_CLIENT_ID"], CONFIG["OAUTH_CLIENT_SECRET"]]):
        raise ValueError("Missing required OAuth settings: URL, client ID, or client secret")
    
    logger.info(f"OAuth URL: {CONFIG['OAUTH_URL']}")
    logger.info(f"Client ID: {CONFIG['OAUTH_CLIENT_ID'][:4]}****")
    
    payload = {
        "grant_type": "client_credentials",
        "client_id": CONFIG["OAUTH_CLIENT_ID"],
        "client_secret": CONFIG["OAUTH_CLIENT_SECRET"],
    }
    
    attempts = 0
    start_time = time.time()
    
    while attempts < CONFIG["MAX_RETRY_ATTEMPTS"]:
        attempts += 1
        attempt_start = time.time()
        
        try:
            logger.info(f"OAuth attempt {attempts}/{CONFIG['MAX_RETRY_ATTEMPTS']}")
            
            response = requests.post(
                CONFIG["OAUTH_URL"], 
                data=payload, 
                timeout=CONFIG["REQUEST_TIMEOUT"]
            )
            response.raise_for_status()
            
            attempt_time = time.time() - attempt_start
            logger.info(f"OAuth response received in {attempt_time:.2f} seconds")
            
            token_data = response.json()
            token = token_data.get("access_token")
            
            if not token:
                raise ValueError("OAuth token not found in response")
            
            # Create token preview for logging
            token_preview = (
                token[:CONFIG["TOKEN_PREVIEW_LENGTH"]] + "..."
                if len(token) > CONFIG["TOKEN_PREVIEW_LENGTH"]
                else token
            )
            logger.info(f"Successfully obtained OAuth token: {token_preview}")
            
            total_time = time.time() - start_time
            logger.info(f"OAuth completed in {total_time:.2f} seconds after {attempts} attempt(s)")
            
            return str(token)
            
        except Exception as e:
            attempt_time = time.time() - attempt_start
            logger.warning(f"OAuth attempt {attempts} failed after {attempt_time:.2f} seconds: {e}")
            
            if attempts < CONFIG["MAX_RETRY_ATTEMPTS"]:
                logger.info(f"Retrying in {CONFIG['RETRY_DELAY_SECONDS']} seconds...")
                time.sleep(CONFIG["RETRY_DELAY_SECONDS"])
    
    raise Exception(f"Failed to obtain OAuth token after {attempts} attempts")

def test_openai_client(oauth_token: str) -> bool:
    """Test OpenAI client connection like iris-project."""
    try:
        from openai import OpenAI
        
        logger.info("Testing OpenAI client connection...")
        
        # Create client like iris-project does
        client = OpenAI(
            api_key=oauth_token,
            base_url=CONFIG["BASE_URL"]
        )
        
        # Log connection details
        token_preview = (
            oauth_token[:CONFIG["TOKEN_PREVIEW_LENGTH"]] + "..."
            if len(oauth_token) > CONFIG["TOKEN_PREVIEW_LENGTH"]
            else oauth_token
        )
        logger.info(f"Using OAuth token: {token_preview}")
        logger.info(f"Using API base URL: {CONFIG['BASE_URL']}")
        
        # Simple test call
        messages = [{"role": "user", "content": "Hello! Please respond with exactly: 'Connection successful'"}]
        
        logger.info("Making test API call...")
        response = client.chat.completions.create(
            model=CONFIG["MODEL_SMALL"],
            messages=messages,
            timeout=CONFIG["REQUEST_TIMEOUT"]
        )
        
        if response and response.choices:
            content = response.choices[0].message.content
            logger.info(f"API Response: {content}")
            
            # Log usage if available
            if hasattr(response, 'usage') and response.usage:
                logger.info(f"Token usage - Prompt: {response.usage.prompt_tokens}, "
                          f"Completion: {response.usage.completion_tokens}")
            
            return "successful" in content.lower()
        else:
            logger.error("No response content received")
            return False
            
    except Exception as e:
        logger.error(f"OpenAI client test failed: {e}")
        return False

def test_streaming(oauth_token: str) -> bool:
    """Test streaming response like iris-project."""
    try:
        from openai import OpenAI
        
        logger.info("Testing streaming response...")
        
        client = OpenAI(
            api_key=oauth_token,
            base_url=CONFIG["BASE_URL"]
        )
        
        messages = [{"role": "user", "content": "Count from 1 to 5, one number per line."}]
        
        stream = client.chat.completions.create(
            model=CONFIG["MODEL_SMALL"],
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
            timeout=CONFIG["REQUEST_TIMEOUT"]
        )
        
        chunks_received = 0
        content_chunks = []
        
        for chunk in stream:
            chunks_received += 1
            if chunk.choices and chunk.choices[0].delta.content:
                content_chunks.append(chunk.choices[0].delta.content)
            
            # Log usage if in final chunk
            if hasattr(chunk, 'usage') and chunk.usage:
                logger.info(f"Stream usage - Prompt: {chunk.usage.prompt_tokens}, "
                          f"Completion: {chunk.usage.completion_tokens}")
            
            # Reasonable limit
            if chunks_received > 50:
                break
        
        full_content = ''.join(content_chunks)
        logger.info(f"Streaming test - received {chunks_received} chunks")
        logger.info(f"Content preview: {full_content[:100]}...")
        
        return chunks_received > 1
        
    except Exception as e:
        logger.error(f"Streaming test failed: {e}")
        return False

def test_tool_calling(oauth_token: str) -> bool:
    """Test tool calling functionality."""
    try:
        from openai import OpenAI
        
        logger.info("Testing tool calling...")
        
        client = OpenAI(
            api_key=oauth_token,
            base_url=CONFIG["BASE_URL"]
        )
        
        # Define a simple test tool
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the current weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state/country"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        
        messages = [{"role": "user", "content": "What's the weather like in Toronto?"}]
        
        response = client.chat.completions.create(
            model=CONFIG["MODEL_SMALL"],
            messages=messages,
            tools=tools,
            timeout=CONFIG["REQUEST_TIMEOUT"]
        )
        
        if response and response.choices:
            message = response.choices[0].message
            
            # Check for tool calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                logger.info(f"Tool calls detected: {len(message.tool_calls)}")
                for tool_call in message.tool_calls:
                    logger.info(f"Tool: {tool_call.function.name}, Args: {tool_call.function.arguments}")
                return True
            else:
                logger.info(f"No tool calls detected. Response: {message.content[:100]}...")
                return False
        
        return False
        
    except Exception as e:
        logger.error(f"Tool calling test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("COMPLETE COHERE MODEL TEST")
    print("=" * 60)
    print("Replicating iris-project authentication flow:")
    print("1. SSL setup")
    print("2. OAuth authentication") 
    print("3. OpenAI client with cohere model")
    print("4. Streaming and tool calling tests")
    print()
    
    try:
        # Step 1: Setup SSL
        print("STEP 1: SSL SETUP")
        print("-" * 30)
        cert_path = setup_ssl()
        
        # Step 2: OAuth Authentication
        print("\nSTEP 2: OAUTH AUTHENTICATION")
        print("-" * 30)
        oauth_token = setup_oauth()
        
        # Step 3: Test OpenAI Client
        print("\nSTEP 3: OPENAI CLIENT TEST")
        print("-" * 30)
        basic_success = test_openai_client(oauth_token)
        
        # Step 4: Test Streaming
        print("\nSTEP 4: STREAMING TEST")
        print("-" * 30)
        streaming_success = test_streaming(oauth_token)
        
        # Step 5: Test Tool Calling
        print("\nSTEP 5: TOOL CALLING TEST")
        print("-" * 30)
        tools_success = test_tool_calling(oauth_token)
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        tests = [
            ("SSL Setup", cert_path is not None),
            ("OAuth Authentication", True),  # If we got here, OAuth worked
            ("Basic API Connection", basic_success),
            ("Streaming", streaming_success),
            ("Tool Calling", tools_success)
        ]
        
        for test_name, result in tests:
            status = "✓" if result else "✗"
            print(f"{status} {test_name}: {'PASSED' if result else 'FAILED'}")
        
        successful_tests = sum(1 for _, result in tests if result)
        total_tests = len(tests)
        
        print(f"\nCohere Integration: {successful_tests}/{total_tests} tests passed")
        
        if successful_tests == total_tests:
            print("\n✓ SUCCESS: Complete cohere integration working!")
            print("  Ready to build web research with LLM synthesis.")
        elif successful_tests >= 3:  # SSL, OAuth, Basic API
            print("\n⚠ PARTIAL: Core functionality working")
            print("  Can proceed with basic web research capabilities.")
        else:
            print("\n✗ FAILED: Core integration issues")
            print("  Check configuration and network connectivity.")
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        print(f"\n✗ FAILED: {e}")
        print("\nTroubleshooting:")
        print("1. Update CONFIG section with your actual endpoints and credentials")
        print("2. Ensure SSL certificate is in ssl_certs/rbc-ca-bundle.cer")
        print("3. Check network connectivity and OAuth configuration")

if __name__ == "__main__":
    main()