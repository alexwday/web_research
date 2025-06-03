"""
Test script for Crawl4AI web scraping with SSL certificate support
This script tests various crawling scenarios including JavaScript rendering,
dynamic content, and integration with our SSL certificate setup.
"""

import asyncio
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy
import json

# SSL certificate path
SSL_CERT_PATH = os.path.join(os.path.dirname(__file__), 'ssl_certs', 'rbc-ca-bundle.cer')

async def test_basic_crawl():
    """Test basic crawling functionality"""
    print("\n=== Testing Basic Crawl ===")
    
    # Configure browser with SSL handling
    browser_config = BrowserConfig(
        headless=True,
        extra_args=[
            '--ignore-certificate-errors',
            '--allow-insecure-localhost'
        ] if not os.path.exists(SSL_CERT_PATH) else []
    )
    
    async with AsyncWebCrawler(browser_config=browser_config) as crawler:
        # Test a simple website
        result = await crawler.arun(
            url="https://example.com",
            bypass_cache=True
        )
        
        print(f"Status: {result.success}")
        print(f"Title: {result.metadata.get('title', 'N/A')}")
        print(f"Content length: {len(result.markdown) if result.markdown else 0}")
        print(f"First 200 chars of markdown: {result.markdown[:200] if result.markdown else 'No content'}...")
        
        return result

async def test_javascript_rendering():
    """Test JavaScript rendering capabilities"""
    print("\n=== Testing JavaScript Rendering ===")
    
    browser_config = BrowserConfig(
        headless=True,
        java_script_enabled=True
    )
    
    run_config = CrawlerRunConfig(
        wait_for="css:body",  # Wait for body to load
        delay_before_return_html=2.0  # Wait 2 seconds for JS to execute
    )
    
    async with AsyncWebCrawler(browser_config=browser_config) as crawler:
        # Test on a site with dynamic content
        result = await crawler.arun(
            url="https://httpbin.org/delay/1",
            config=run_config,
            bypass_cache=True
        )
        
        print(f"Status: {result.success}")
        print(f"JavaScript executed: {result.metadata.get('js_executed', False)}")
        print(f"Page loaded in: {result.metadata.get('load_time', 'N/A')}ms")
        
        return result

async def test_structured_extraction():
    """Test structured data extraction using CSS selectors"""
    print("\n=== Testing Structured Extraction ===")
    
    # Define extraction schema for news/article sites
    schema = {
        "name": "Article Extractor",
        "baseSelector": "body",
        "fields": [
            {
                "name": "title",
                "selector": "h1",
                "type": "text"
            },
            {
                "name": "paragraphs",
                "selector": "p",
                "type": "list",
                "fields": [
                    {
                        "name": "text",
                        "type": "text"
                    }
                ]
            },
            {
                "name": "links",
                "selector": "a[href]",
                "type": "list",
                "fields": [
                    {
                        "name": "text",
                        "type": "text"
                    },
                    {
                        "name": "href",
                        "type": "attribute",
                        "attribute": "href"
                    }
                ]
            }
        ]
    }
    
    extraction_strategy = JsonCssExtractionStrategy(schema)
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com",
            extraction_strategy=extraction_strategy,
            bypass_cache=True
        )
        
        print(f"Status: {result.success}")
        if result.extracted_content:
            data = json.loads(result.extracted_content)
            print(f"Extracted title: {data[0].get('title', 'N/A') if data else 'N/A'}")
            print(f"Number of paragraphs: {len(data[0].get('paragraphs', [])) if data else 0}")
            print(f"Number of links: {len(data[0].get('links', [])) if data else 0}")
        
        return result

async def test_multiple_urls():
    """Test crawling multiple URLs concurrently"""
    print("\n=== Testing Multiple URL Crawling ===")
    
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://httpbin.org/json"
    ]
    
    browser_config = BrowserConfig(
        headless=True,
        extra_args=['--ignore-certificate-errors']
    )
    
    async with AsyncWebCrawler(browser_config=browser_config) as crawler:
        tasks = [crawler.arun(url=url, bypass_cache=True) for url in urls]
        results = await asyncio.gather(*tasks)
        
        for i, (url, result) in enumerate(zip(urls, results)):
            print(f"\nURL {i+1}: {url}")
            print(f"  Status: {result.success}")
            print(f"  Content length: {len(result.markdown) if result.markdown else 0}")
        
        return results

async def test_with_ssl_sites():
    """Test crawling sites that might have SSL certificate issues"""
    print("\n=== Testing SSL Certificate Handling ===")
    
    # Sites that commonly have enterprise SSL cert issues
    test_sites = [
        "https://github.com",
        "https://www.google.com",
        "https://stackoverflow.com"
    ]
    
    browser_config = BrowserConfig(
        headless=True,
        extra_args=[
            '--ignore-certificate-errors',
            '--allow-insecure-localhost',
            f'--ssl-cert-dir={os.path.dirname(SSL_CERT_PATH)}' if os.path.exists(SSL_CERT_PATH) else ''
        ]
    )
    
    async with AsyncWebCrawler(browser_config=browser_config) as crawler:
        for site in test_sites:
            print(f"\nTesting {site}...")
            try:
                result = await crawler.arun(
                    url=site,
                    bypass_cache=True,
                    config=CrawlerRunConfig(
                        delay_before_return_html=1.0
                    )
                )
                print(f"  Success: {result.success}")
                print(f"  SSL handled: {'Yes' if result.success else 'No'}")
            except Exception as e:
                print(f"  Error: {str(e)}")

async def main():
    """Run all tests"""
    print("Starting Crawl4AI Tests...")
    print(f"SSL Certificate exists: {os.path.exists(SSL_CERT_PATH)}")
    
    try:
        # Run tests
        await test_basic_crawl()
        await test_javascript_rendering()
        await test_structured_extraction()
        await test_multiple_urls()
        await test_with_ssl_sites()
        
        print("\n=== All Tests Completed ===")
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run async tests
    asyncio.run(main())