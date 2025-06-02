#!/usr/bin/env python3
"""
Cohere Model Test
Tests connection to the cohere_testing framework with streaming and tool calling.
Assumes cohere_testing project is available at ../cohere_testing/
"""

import sys
import os
from pathlib import Path
import logging

# Set up simple logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def setup_cohere_path():
    """Add cohere_testing to Python path."""
    # Look for cohere_testing in common locations
    search_paths = [
        "../cohere_testing",
        "../../cohere_testing", 
        "/Users/alexwday/Projects/cohere_testing"
    ]
    
    for path in search_paths:
        cohere_path = Path(path).resolve()
        if cohere_path.exists() and (cohere_path / "cohere").exists():
            logger.info(f"Found cohere_testing at: {cohere_path}")
            sys.path.insert(0, str(cohere_path))
            return True
    
    logger.error("Could not find cohere_testing project")
    return False

def test_basic_model_connection():
    """Test basic model connection and response."""
    try:
        from cohere.src.chat_model.model import model
        
        logger.info("Testing basic model connection...")
        
        # Simple test conversation
        conversation = [{"role": "user", "content": "Hello! Please respond with exactly: 'Connection successful'"}]
        
        response_text = ""
        token_count = 0
        
        for chunk in model(conversation, capability="small", debug=False):
            if chunk.get("delta"):
                response_text += chunk["delta"]
                token_count += 1
        
        logger.info(f"Response: {response_text.strip()}")
        logger.info(f"Tokens received: {token_count}")
        
        return "Connection successful" in response_text.lower() or "successful" in response_text.lower()
        
    except Exception as e:
        logger.error(f"Basic model test failed: {e}")
        return False

def test_streaming():
    """Test streaming response."""
    try:
        from cohere.src.chat_model.model import model
        
        logger.info("Testing streaming response...")
        
        conversation = [{"role": "user", "content": "Count from 1 to 5, one number per line."}]
        
        chunks_received = 0
        response_text = ""
        
        for chunk in model(conversation, capability="small", debug=False):
            chunks_received += 1
            if chunk.get("delta"):
                response_text += chunk["delta"]
                
            # Stop after reasonable number of chunks
            if chunks_received > 50:
                break
        
        logger.info(f"Streaming test - chunks received: {chunks_received}")
        logger.info(f"Response preview: {response_text[:100]}...")
        
        return chunks_received > 1  # Should get multiple chunks for streaming
        
    except Exception as e:
        logger.error(f"Streaming test failed: {e}")
        return False

def test_tool_calling():
    """Test tool calling functionality."""
    try:
        from cohere.src.chat_model.model import model
        
        logger.info("Testing tool calling...")
        
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
        
        conversation = [
            {"role": "user", "content": "What's the weather like in Toronto?"}
        ]
        
        response_text = ""
        tool_calls_found = False
        
        for chunk in model(conversation, capability="small", tools=tools, debug=False):
            if chunk.get("delta"):
                response_text += chunk["delta"]
            
            # Check for tool calls in the chunk
            if chunk.get("tool_calls") or "get_weather" in str(chunk):
                tool_calls_found = True
                logger.info(f"Tool call detected in chunk: {chunk}")
                break
        
        logger.info(f"Tool calling test - tool calls found: {tool_calls_found}")
        logger.info(f"Response: {response_text[:200]}...")
        
        return tool_calls_found
        
    except Exception as e:
        logger.error(f"Tool calling test failed: {e}")
        return False

def test_conversation_format():
    """Test different conversation formats."""
    try:
        from cohere.src.chat_model.model import model
        
        logger.info("Testing conversation format handling...")
        
        # Multi-turn conversation
        conversation = [
            {"role": "user", "content": "My name is Alex"},
            {"role": "assistant", "content": "Nice to meet you, Alex!"},
            {"role": "user", "content": "What's my name?"}
        ]
        
        response_text = ""
        for chunk in model(conversation, capability="small", debug=False):
            if chunk.get("delta"):
                response_text += chunk["delta"]
        
        logger.info(f"Multi-turn response: {response_text.strip()}")
        
        # Should remember the name from earlier in conversation
        return "alex" in response_text.lower()
        
    except Exception as e:
        logger.error(f"Conversation format test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("COHERE MODEL TEST")
    print("=" * 60)
    
    # Setup cohere_testing path
    if not setup_cohere_path():
        print("❌ Could not find cohere_testing project")
        print("Make sure cohere_testing is available at ../cohere_testing/")
        return
    
    print("\nTesting cohere model connection and capabilities...")
    print("-" * 60)
    
    tests = [
        ("Basic Connection", test_basic_model_connection),
        ("Streaming", test_streaming), 
        ("Tool Calling", test_tool_calling),
        ("Conversation Format", test_conversation_format)
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"Running {test_name} test...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"{test_name} test error: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    successful_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = "✓" if result else "✗"
        print(f"{status} {test_name}: {'PASSED' if result else 'FAILED'}")
    
    print(f"\nCohere Model Tests: {successful_tests}/{total_tests} passed")
    
    if successful_tests == total_tests:
        print("\n✓ SUCCESS: All cohere model capabilities working!")
        print("  Ready to build web research with LLM synthesis.")
    elif successful_tests > 0:
        print(f"\n⚠ PARTIAL: {successful_tests} capabilities working")
        print("  Can proceed with limited functionality.")
    else:
        print("\n✗ FAILED: No cohere model connectivity")
        print("  Check cohere_testing project setup.")
    
    print("\nThis test confirms LLM capabilities for the research framework.")

if __name__ == "__main__":
    main()