import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import hashlib
from config import MODEL_NAME, MAX_SEARCH_RESULTS, MAX_CONTENT_LENGTH, REQUEST_TIMEOUT
import urllib3


class ResearchNote:
    def __init__(self, content: str, source_url: Optional[str] = None):
        self.id = hashlib.md5(f"{content}{source_url}{datetime.now()}".encode()).hexdigest()[:8]
        self.content = content
        self.source_url = source_url
        self.timestamp = datetime.now()
        self.title = self._extract_title()
    
    def _extract_title(self) -> str:
        if self.source_url:
            domain = urlparse(self.source_url).netloc
            return f"Note from {domain}"
        return "General Note"
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'source_url': self.source_url,
            'timestamp': self.timestamp.isoformat(),
            'title': self.title
        }


class ResearchAgent:
    def __init__(self, oauth_config: Dict[str, str], ssl_cert_path: str):
        self.oauth_config = oauth_config
        self.ssl_cert_path = ssl_cert_path
        self.notes: List[ResearchNote] = []
        self.sources: Dict[str, Dict[str, Any]] = {}  # url -> {content, title, timestamp}
        self.client = None
        
        # Setup SSL certificate
        import os
        if not os.path.exists(ssl_cert_path):
            print(f"WARNING: SSL certificate not found at {ssl_cert_path}")
        else:
            print(f"SSL certificate found at {ssl_cert_path}")
            # Set environment variables for SSL
            os.environ["SSL_CERT_FILE"] = ssl_cert_path
            os.environ["REQUESTS_CA_BUNDLE"] = ssl_cert_path
            print("SSL environment variables configured")
            
        self._init_client()
    
    def _init_client(self):
        try:
            # Get OAuth token
            token = self._get_oauth_token()
            
            # Initialize OpenAI client with Cohere
            print(f"Initializing OpenAI client with base URL: {self.oauth_config['base_url']}")
            self.client = OpenAI(
                api_key=token,
                base_url=self.oauth_config['base_url']
            )
            print("OpenAI client initialized successfully")
        except Exception as e:
            print(f"Failed to initialize client: {e}")
            raise
    
    def _get_oauth_token(self) -> str:
        try:
            print(f"Attempting OAuth authentication to: {self.oauth_config['oauth_url']}")
            response = requests.post(
                self.oauth_config['oauth_url'],
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.oauth_config['client_id'],
                    'client_secret': self.oauth_config['client_secret']
                },
                verify=self.ssl_cert_path,
                timeout=30
            )
            response.raise_for_status()
            token_data = response.json()
            print("OAuth token obtained successfully")
            return token_data['access_token']
        except requests.exceptions.RequestException as e:
            print(f"OAuth request failed: {e}")
            raise
        except KeyError as e:
            print(f"OAuth response missing expected field: {e}")
            print(f"Response: {response.text}")
            raise
    
    def _is_problematic_site(self, url: str) -> bool:
        """Check if URL is known to have SSL issues."""
        problematic_sites = ['github.com', 'githubusercontent.com']
        return any(site in url for site in problematic_sites)
    
    def _fetch_with_urllib3(self, url: str) -> requests.Response:
        """Fetch URL using urllib3 with relaxed SSL validation."""
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        http = urllib3.PoolManager(
            cert_reqs='CERT_NONE', 
            assert_hostname=False, 
            timeout=urllib3.Timeout(connect=REQUEST_TIMEOUT, read=REQUEST_TIMEOUT)
        )
        response = http.request('GET', url, headers={'User-Agent': 'Mozilla/5.0'})
        
        # Convert urllib3 response to requests-like response
        class FakeResponse:
            def __init__(self, data, status):
                self.text = data.decode('utf-8')
                self.status_code = status
                self.content = data
                
        return FakeResponse(response.data, response.status)
    
    def search_web(self, query: str) -> Dict[str, Any]:
        """Search the web and store results with sources"""
        try:
            # For prototype, we'll use DuckDuckGo HTML search
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            
            # DuckDuckGo doesn't typically have SSL issues, but use standard approach
            response = requests.get(
                search_url,
                headers={'User-Agent': 'Mozilla/5.0'},
                verify=self.ssl_cert_path,
                timeout=REQUEST_TIMEOUT
            )
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.find_all('div', class_='result')[:MAX_SEARCH_RESULTS]:
                link_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if link_elem and link_elem.get('href'):
                    url = link_elem['href']
                    title = link_elem.get_text(strip=True)
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        'url': url,
                        'title': title,
                        'snippet': snippet
                    })
                    
                    # Store source
                    self.sources[url] = {
                        'title': title,
                        'snippet': snippet,
                        'timestamp': datetime.now().isoformat(),
                        'query': query
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
    
    def fetch_page_content(self, url: str) -> Dict[str, Any]:
        """Fetch and parse content from a specific URL"""
        try:
            # Use dual strategy for problematic sites
            if self._is_problematic_site(url):
                print(f"Using urllib3 for problematic site: {url}")
                response = self._fetch_with_urllib3(url)
            else:
                response = requests.get(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0'},
                    verify=self.ssl_cert_path,
                    timeout=REQUEST_TIMEOUT
                )
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit text length
            text = text[:MAX_CONTENT_LENGTH] + "..." if len(text) > MAX_CONTENT_LENGTH else text
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else urlparse(url).netloc
            
            # Update source with full content
            self.sources[url] = {
                'title': title_text,
                'content': text,
                'timestamp': datetime.now().isoformat(),
                'url': url
            }
            
            return {
                'success': True,
                'url': url,
                'title': title_text,
                'content': text
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
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call"""
        if tool_name == "search_web":
            return self.search_web(arguments['query'])
        elif tool_name == "fetch_page_content":
            return self.fetch_page_content(arguments['url'])
        elif tool_name == "take_note":
            return self.take_note(
                arguments['content'],
                arguments.get('source_url')
            )
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
    
    def process_message(self, user_message: str) -> Dict[str, Any]:
        """Process a user message and return response with sources"""
        try:
            print(f"Processing message: {user_message[:50]}...")
            
            messages = [
                {
                    "role": "system",
                    "content": """You are a helpful research assistant. When answering questions:
1. Search for relevant information if needed
2. Take notes on important findings with source URLs
3. Provide comprehensive answers with citations
4. Format citations as [1], [2], etc. in your response
5. Always cite your sources when using web information"""
                },
                {"role": "user", "content": user_message}
            ]
            
            # Create completion with tools
            print(f"Calling {MODEL_NAME} with tools...")
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=self.get_tools()
            )
            print("Initial completion successful")
            
            # Process tool calls
            tool_calls = []
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    # Execute tool
                    result = self.execute_tool(tool_name, arguments)
                    tool_calls.append({
                        'tool': tool_name,
                        'arguments': arguments,
                        'result': result
                    })
                    
                    # Add tool result to messages
                    messages.append(response.choices[0].message)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })
                
                # Get final response after tool use
                final_response = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages
                )
                
                response_text = final_response.choices[0].message.content
            else:
                response_text = response.choices[0].message.content
            
            # Extract citations and create source list
            citation_pattern = r'\[(\d+)\]'
            citations = list(set(re.findall(citation_pattern, response_text)))
            
            # Map citations to sources
            source_list = []
            for i, note in enumerate(self.notes):
                if note.source_url:
                    source_list.append({
                        'citation': f"[{i+1}]",
                        'url': note.source_url,
                        'title': self.sources.get(note.source_url, {}).get('title', note.title)
                    })
            
            return {
                'response': response_text,
                'sources': source_list,
                'tool_calls': tool_calls,
                'notes': [note.to_dict() for note in self.notes]
            }
        except Exception as e:
            print(f"Error in process_message: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def clear_session(self):
        """Clear notes and sources for a new session"""
        self.notes.clear()
        self.sources.clear()