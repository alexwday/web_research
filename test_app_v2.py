"""
Test script for Web Research Framework v2
Tests the complete integration of Crawl4AI, OAuth, and Cohere LLM
"""

import asyncio
import os
from app_v2 import scraper, analyzer, token_manager
from crawl4ai import CacheMode

async def test_oauth():
    """Test OAuth token acquisition"""
    print("\n=== Testing OAuth ===")
    try:
        token = await token_manager.get_token()
        print(f"✅ OAuth token acquired: {token[:20]}...")
        return True
    except Exception as e:
        print(f"❌ OAuth failed: {e}")
        return False

async def test_web_scraping():
    """Test Crawl4AI web scraping"""
    print("\n=== Testing Web Scraping ===")
    try:
        result = await scraper.scrape("https://example.com")
        print(f"✅ Scraped successfully")
        print(f"  Title: {result['title']}")
        print(f"  Content length: {len(result['markdown'])}")
        return True
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return False

async def test_llm_analysis():
    """Test LLM analysis"""
    print("\n=== Testing LLM Analysis ===")
    try:
        # First scrape some content
        scrape_result = await scraper.scrape("https://example.com")
        
        # Then analyze it
        analysis = await analyzer.analyze(
            scrape_result['markdown'],
            "What is the main purpose of this website?",
            max_tokens=500
        )
        
        print(f"✅ LLM analysis successful")
        print(f"  Response length: {len(analysis)}")
        print(f"  First 200 chars: {analysis[:200]}...")
        return True
    except Exception as e:
        print(f"❌ LLM analysis failed: {e}")
        return False

async def test_structured_extraction():
    """Test structured data extraction"""
    print("\n=== Testing Structured Extraction ===")
    
    schema = {
        "name": "WebsiteInfo",
        "baseSelector": "body",
        "fields": [
            {"name": "title", "selector": "h1", "type": "text"},
            {"name": "paragraphs", "selector": "p", "type": "list", "fields": [
                {"name": "text", "type": "text"}
            ]}
        ]
    }
    
    try:
        result = await scraper.scrape("https://example.com", schema)
        print(f"✅ Structured extraction successful")
        if result['extracted_content']:
            print(f"  Extracted data: {result['extracted_content'][0]}")
        return True
    except Exception as e:
        print(f"❌ Structured extraction failed: {e}")
        return False

async def test_full_pipeline():
    """Test the complete research pipeline"""
    print("\n=== Testing Full Pipeline ===")
    
    test_cases = [
        {
            "url": "https://example.com",
            "query": "What is this website about?"
        },
        {
            "url": "https://httpbin.org/html",
            "query": "What information does this page contain?"
        }
    ]
    
    for i, test in enumerate(test_cases):
        print(f"\nTest case {i+1}: {test['url']}")
        try:
            # Scrape
            scrape_result = await scraper.scrape(test['url'])
            print(f"  ✅ Scraped: {scrape_result['title']}")
            
            # Analyze
            analysis = await analyzer.analyze(
                scrape_result['markdown'],
                test['query'],
                max_tokens=500
            )
            print(f"  ✅ Analyzed: {len(analysis)} chars")
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")

async def main():
    """Run all tests"""
    print("🧪 Web Research Framework v2 - Integration Tests")
    print(f"SSL Certificate exists: {os.path.exists('ssl_certs/rbc-ca-bundle.cer')}")
    
    # Check configuration
    try:
        from config import OAUTH_CONFIG
        if OAUTH_CONFIG['client_id'] == 'YOUR_CLIENT_ID_HERE':
            print("\n⚠️  Configuration not updated!")
            print("Please edit config.py before running tests")
            return
    except ImportError:
        print("\n❌ Failed to import config.py")
        return
    
    # Run tests
    tests = [
        ("OAuth", test_oauth),
        ("Web Scraping", test_web_scraping),
        ("LLM Analysis", test_llm_analysis),
        ("Structured Extraction", test_structured_extraction),
        ("Full Pipeline", test_full_pipeline)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Summary")
    print("="*50)
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:.<30} {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} passed")

if __name__ == "__main__":
    asyncio.run(main())