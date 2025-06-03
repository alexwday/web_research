"""
Research Agent v2 - Enhanced with Crawl4AI for better web scraping
Maintains conversational context and uses advanced browser automation
"""

import asyncio
import json
import re
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlparse, quote_plus
import uuid

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from openai import OpenAI
import httpx

from config import (
    SSL_CERT_PATH,
    OAUTH_CONFIG,
    MODEL_NAME,
    MAX_TOKENS,
    MAX_SEARCH_RESULTS,
    MAX_CONTENT_LENGTH,
    REQUEST_TIMEOUT
)


class ResearchNote:
    """Simple note structure for research findings"""
    def __init__(self, content: str, source_url: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.content = content
        self.source_url = source_url
        self.timestamp = datetime.now().isoformat()
        
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'source_url': self.source_url,
            'timestamp': self.timestamp
        }


class ResearchAgentV2:
    """Enhanced research agent using Crawl4AI for web scraping"""
    
    def __init__(self, oauth_token: str):
        self.sources = {}
        self.notes = []
        self.conversation_history = []
        self.url_index = {}  # Maps URLs to index numbers
        self.index_counter = 0  # Counter for generating unique indices
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=oauth_token,
            base_url=OAUTH_CONFIG['base_url'],
            http_client=httpx.Client(verify=SSL_CERT_PATH if os.path.exists(SSL_CERT_PATH) else True)
        )
        
        # Configure Crawl4AI browser
        self.browser_config = BrowserConfig(
            headless=True,
            java_script_enabled=True,
            extra_args=[
                '--ignore-certificate-errors',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        # Cache for web crawler instance
        self._crawler = None
    
    def get_url_index(self, url: str) -> int:
        """Get or create an index for a URL"""
        if url not in self.url_index:
            self.index_counter += 1
            self.url_index[url] = self.index_counter
        return self.url_index[url]
    
    def get_url_by_index(self, index: int) -> Optional[str]:
        """Get URL by index number"""
        for url, idx in self.url_index.items():
            if idx == index:
                return url
        return None
    
    async def get_crawler(self):
        """Get or create web crawler instance"""
        if not self._crawler:
            self._crawler = AsyncWebCrawler(config=self.browser_config)
            await self._crawler.__aenter__()
        return self._crawler
    
    async def close(self):
        """Clean up resources"""
        if self._crawler:
            await self._crawler.__aexit__(None, None, None)
            self._crawler = None
    
    async def search_web(self, query: str) -> Dict[str, Any]:
        """Search the web using DuckDuckGo through Crawl4AI"""
        try:
            # Use DuckDuckGo HTML interface
            search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
            
            crawler = await self.get_crawler()
            result = await crawler.arun(
                url=search_url,
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    wait_for="css:.result",
                    delay_before_return_html=1.0
                )
            )
            
            if not result.success:
                return {
                    'success': False,
                    'error': 'Failed to perform search',
                    'query': query
                }
            
            # Parse search results from HTML
            import re
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(result.html, 'html.parser')
            results = []
            
            # Find search result divs
            for result_div in soup.select('.result')[:MAX_SEARCH_RESULTS]:
                # Extract URL
                link_elem = result_div.select_one('.result__url')
                if not link_elem:
                    continue
                    
                url = link_elem.get_text(strip=True)
                if not url.startswith('http'):
                    url = 'https://' + url
                
                # Extract title
                title_elem = result_div.select_one('.result__title')
                title = title_elem.get_text(strip=True) if title_elem else 'No title'
                
                # Extract snippet
                snippet_elem = result_div.select_one('.result__snippet')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else 'No description'
                
                # Get URL index
                url_index = self.get_url_index(url)
                
                results.append({
                    'url': url,
                    'title': title,
                    'snippet': snippet,
                    'index': url_index
                })
                
                # Store source
                self.sources[url] = {
                    'title': title,
                    'snippet': snippet,
                    'timestamp': datetime.now().isoformat(),
                    'query': query,
                    'index': url_index
                }
            
            return {
                'success': True,
                'results': results,
                'query': query
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    async def fetch_page_content(self, url: str) -> Dict[str, Any]:
        """Fetch and parse content from a specific URL using Crawl4AI"""
        try:
            crawler = await self.get_crawler()
            
            # Content extraction configuration
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                wait_for="css:body",
                delay_before_return_html=1.0
            )
            
            result = await crawler.arun(url=url, config=run_config)
            
            if not result.success:
                return {
                    'success': False,
                    'url': url,
                    'error': 'Failed to fetch page'
                }
            
            # Process for agent consumption
            content = result.markdown
            if len(content) > MAX_CONTENT_LENGTH:
                content = content[:MAX_CONTENT_LENGTH] + "..."
            
            title = result.metadata.get('title', urlparse(url).netloc)
            
            # Get URL index
            url_index = self.get_url_index(url)
            
            # Update source with full content
            self.sources[url] = {
                'title': title,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'index': url_index
            }
            
            return {
                'success': True,
                'url': url,
                'title': title,
                'content': content
            }
                
        except Exception as e:
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }
    
    def take_note(self, content: str, source_url: Optional[str] = None) -> Dict[str, Any]:
        """Store a research note"""
        note = ResearchNote(content, source_url)
        self.notes.append(note)
        
        return {
            'success': True,
            'note_id': note.id,
            'message': 'Note saved successfully'
        }
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return tool definitions for the LLM"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fetch_page_content",
                    "description": "Fetch detailed content from a specific webpage",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to fetch content from"
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "take_note",
                    "description": "Save a research note for later synthesis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The note content"
                            },
                            "source_url": {
                                "type": "string",
                                "description": "Optional source URL for the note"
                            }
                        },
                        "required": ["content"]
                    }
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call"""
        if tool_name == "search_web":
            return await self.search_web(arguments['query'])
        elif tool_name == "fetch_page_content":
            return await self.fetch_page_content(arguments['url'])
        elif tool_name == "take_note":
            return self.take_note(
                arguments['content'],
                arguments.get('source_url')
            )
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
    
    async def process_message(self, user_message: str, status_callback=None) -> Dict[str, Any]:
        """Process a user message and return response with sources"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": """You are a helpful research assistant with access to web search and browsing capabilities. When answering questions:
1. Search for relevant information if needed
2. Fetch detailed content from promising sources  
3. Take notes on important findings with source URLs
4. Provide comprehensive answers with index-based citations
5. Use LINK_INDEX format: LINK_INDEX:1, LINK_INDEX:2, etc. for citations
6. NEVER write full URLs in your response - only use LINK_INDEX numbers
7. Keep responses concise and focused
8. The system will automatically convert LINK_INDEX numbers to clickable links

Example: "According to recent data LINK_INDEX:1, AI adoption is growing rapidly LINK_INDEX:2."

You have access to advanced web scraping that can handle JavaScript-heavy sites and bypass most restrictions."""
                },
                {"role": "user", "content": user_message}
            ]
            
            # Get response with tools
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=self.get_tools(),
                max_tokens=MAX_TOKENS,
                stream=False  # Don't stream initial tool call response
            )
            
            # Process tool calls
            tool_calls_info = []
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    if status_callback:
                        await status_callback(f"Executing {function_name}...")
                    
                    # Execute tool
                    tool_result = await self.execute_tool(function_name, arguments)
                    tool_calls_info.append({
                        'tool': function_name,
                        'arguments': arguments,
                        'result': tool_result
                    })
                    
                    # Add tool result to messages
                    messages.append(response.choices[0].message)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result)
                    })
                
                # Get final response after tool use with streaming
                if status_callback:
                    await status_callback("Generating response...")
                
                final_response = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    max_tokens=MAX_TOKENS,
                    stream=True
                )
                
                response_text = ""
                for chunk in final_response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        response_text += content
                        if status_callback:
                            # Use asyncio.create_task to handle the async callback
                            asyncio.create_task(status_callback(f"stream_chunk:{content}"))
            else:
                response_text = response.choices[0].message.content
            
            # Extract citations and create source list
            citation_pattern = r'\[(\d+)\]'
            citations = list(set(re.findall(citation_pattern, response_text)))
            
            # Map citations to sources
            source_list = []
            for i, note in enumerate(self.notes):
                if note.source_url and note.source_url in self.sources:
                    source_data = self.sources[note.source_url]
                    source_list.append({
                        'citation': f"[{i+1}]",
                        'url': note.source_url,
                        'title': source_data.get('title', 'Unknown'),
                        'snippet': source_data.get('snippet', source_data.get('content', '')[:200] + '...')
                    })
            
            # Also include sources that were recently fetched but not yet noted
            for url, source_data in list(self.sources.items())[-5:]:  # Last 5 sources
                if not any(s['url'] == url for s in source_list):
                    source_list.append({
                        'url': url,
                        'title': source_data.get('title', 'Unknown'),
                        'snippet': source_data.get('snippet', source_data.get('content', '')[:200] + '...'),
                        'index': source_data.get('index', self.get_url_index(url))
                    })
            
            return {
                'success': True,
                'response': response_text,
                'sources': source_list,
                'notes_count': len(self.notes),
                'tool_calls': tool_calls_info
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'response': f"I encountered an error: {str(e)}"
            }
    
    def reset_conversation(self):
        """Clear conversation history while preserving sources and notes"""
        self.conversation_history = []
        return {'success': True, 'message': 'Conversation reset'}
    
    def get_all_sources(self) -> Dict[str, Any]:
        """Get all collected sources"""
        return self.sources
    
    def get_all_notes(self) -> List[Dict[str, Any]]:
        """Get all research notes"""
        return [note.to_dict() for note in self.notes]