import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs
import hashlib
from config import MODEL_NAME, MAX_SEARCH_RESULTS, MAX_CONTENT_LENGTH, REQUEST_TIMEOUT, MAX_TOKENS
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
        problematic_sites = ['github.com', 'githubusercontent.com', 'td.com', 'tdbank.com']
        return any(site in url for site in problematic_sites)
    
    def _fetch_with_urllib3(self, url: str) -> requests.Response:
        """Fetch URL using urllib3 with relaxed SSL validation."""
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Create a pool manager with completely disabled SSL verification
        http = urllib3.PoolManager(
            cert_reqs='CERT_NONE', 
            assert_hostname=False,
            ca_certs=None,  # Explicitly set to None
            timeout=urllib3.Timeout(connect=REQUEST_TIMEOUT, read=REQUEST_TIMEOUT)
        )
        
        try:
            response = http.request(
                'GET', 
                url, 
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
            )
            
            # Convert urllib3 response to requests-like response
            class FakeResponse:
                def __init__(self, data, status, headers=None):
                    # Handle different content types
                    try:
                        self.text = data.decode('utf-8', errors='replace')
                    except:
                        self.text = str(data)
                    self.status_code = status
                    self.content = data
                    self.headers = headers or {}
                    
            return FakeResponse(response.data, response.status, response.headers)
        except Exception as e:
            print(f"urllib3 request failed: {e}")
            raise
    
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
                    # DuckDuckGo HTML returns URLs in a special format
                    href = link_elem['href']
                    
                    # DuckDuckGo uses /l/?uddg=URL format for external links
                    if '/l/?' in href and ('uddg=' in href or 'kh=' in href):
                        # Handle both /l/ and //duckduckgo.com/l/ formats
                        if href.startswith('//'):
                            full_url = 'https:' + href
                        elif href.startswith('/'):
                            full_url = 'https://duckduckgo.com' + href
                        else:
                            full_url = href
                        
                        # Parse the uddg parameter from the URL
                        parsed = urlparse(full_url)
                        params = parse_qs(parsed.query)
                        if 'uddg' in params and params['uddg']:
                            url = params['uddg'][0]
                            print(f"Extracted URL from uddg: {url}")
                        elif 'kh' in params and params['kh']:
                            url = params['kh'][0]
                            print(f"Extracted URL from kh: {url}")
                        else:
                            print(f"Could not extract URL from DuckDuckGo link: {href}")
                            continue
                    else:
                        # Check for the actual URL in the result__url span
                        url_elem = result.find('span', class_='result__url')
                        if url_elem:
                            # Extract the actual URL from the span text
                            url_text = url_elem.get_text(strip=True)
                            # Clean up the URL
                            if url_text.startswith('https://'):
                                url = url_text
                            elif url_text.startswith('http://'):
                                url = url_text
                            else:
                                # If no protocol, assume https
                                url = 'https://' + url_text
                        else:
                            # Fallback - skip relative URLs
                            if href.startswith('/'):
                                print(f"Skipping relative URL: {href}")
                                continue
                            url = href
                            if url.startswith('//'):
                                url = 'https:' + url
                    
                    title = link_elem.get_text(strip=True)
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    print(f"Found search result: {url}")
                    
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
            # Check if URL is a PDF
            if url.lower().endswith('.pdf'):
                print(f"Detected PDF URL: {url}")
                # For PDFs, we'll just return metadata for now
                return {
                    'success': True,
                    'url': url,
                    'title': 'PDF Document',
                    'content': f'This is a PDF document. Direct PDF viewing is not supported in the preview. Please click "Open in Browser" to view the PDF: {url}'
                }
            
            # Use dual strategy for problematic sites
            if self._is_problematic_site(url):
                print(f"Using urllib3 for problematic site: {url}")
                response = self._fetch_with_urllib3(url)
            else:
                # Try with proper SSL first
                try:
                    # Create a session with SSL adapter
                    session = requests.Session()
                    session.headers.update({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    })
                    
                    response = session.get(
                        url,
                        verify=self.ssl_cert_path,
                        timeout=REQUEST_TIMEOUT,
                        allow_redirects=True
                    )
                except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
                    # If SSL fails, try without verification
                    print(f"SSL/Connection error for {url}: {e}")
                    print("Trying with urllib3 fallback...")
                    response = self._fetch_with_urllib3(url)
            
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
            
        except requests.exceptions.SSLError as e:
            print(f"SSL Error fetching {url}: {e}")
            print("Retrying with urllib3 fallback...")
            try:
                response = self._fetch_with_urllib3(url)
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
            except Exception as e2:
                print(f"urllib3 fallback also failed: {e2}")
                return {
                    'success': False,
                    'url': url,
                    'error': f"SSL Error: {str(e)}; Fallback error: {str(e2)}"
                }
        except Exception as e:
            print(f"Error fetching {url}: {type(e).__name__}: {e}")
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
    
    def process_message(self, user_message: str, status_callback=None) -> Dict[str, Any]:
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
                tools=self.get_tools(),
                max_tokens=MAX_TOKENS
            )
            print("Initial completion successful")
            
            # Process tool calls
            tool_calls = []
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    # Notify about tool usage
                    if status_callback:
                        status_callback('tool_use', {
                            'tool': tool_name,
                            'arguments': arguments
                        })
                    
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
                    messages=messages,
                    max_tokens=MAX_TOKENS
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
    
    async def process_message_stream(self, user_message: str, status_callback=None):
        """Process a user message and stream the response"""
        try:
            print(f"Processing message (streaming): {user_message[:50]}...")
            
            messages = [
                {
                    "role": "system",
                    "content": """You are a helpful research assistant. When answering questions:
1. Search for relevant information if needed
2. Provide comprehensive answers based on the information found
3. When citing sources, use numbered citations like [1], [2], etc. in your response text
4. Do NOT create markdown links or include URLs in your response text
5. Focus on synthesizing the information to answer the user's question thoroughly
6. The numbered sources with clickable links will be provided separately at the bottom"""
                },
                {"role": "user", "content": user_message}
            ]
            
            # First call with tools to gather information
            print(f"Calling {MODEL_NAME} with tools...")
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=self.get_tools(),
                max_tokens=MAX_TOKENS
            )
            
            # Process tool calls and collect sources
            tool_calls = []
            collected_sources = []
            
            if response.choices[0].message.tool_calls:
                # Add the assistant message with tool calls
                messages.append(response.choices[0].message)
                
                for tool_call in response.choices[0].message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    # Notify about tool usage
                    if status_callback:
                        await status_callback('tool_use', {
                            'tool': tool_name,
                            'arguments': arguments
                        })
                    
                    # Execute tool
                    result = self.execute_tool(tool_name, arguments)
                    tool_calls.append({
                        'tool': tool_name,
                        'arguments': arguments,
                        'result': result
                    })
                    
                    # Collect sources from tool results
                    if tool_name == "search_web" and result.get('success'):
                        for search_result in result.get('results', []):
                            collected_sources.append({
                                'url': search_result['url'],
                                'title': search_result['title'],
                                'type': 'search_result'
                            })
                    elif tool_name == "fetch_page_content" and result.get('success'):
                        collected_sources.append({
                            'url': result['url'],
                            'title': result['title'],
                            'type': 'fetched_content'
                        })
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })
                
                # Get final streaming response without tools
                print("Generating final response...")
                stream = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    max_tokens=MAX_TOKENS,
                    stream=True
                )
                
                full_response = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        if status_callback:
                            await status_callback('stream_chunk', {'content': content})
                
                # Send completion with collected sources
                if status_callback:
                    await status_callback('complete', {
                        'response': full_response,
                        'sources': collected_sources,
                        'tool_calls': tool_calls,
                        'notes': [note.to_dict() for note in self.notes]
                    })
                
            else:
                # No tools needed, stream directly
                stream = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    max_tokens=MAX_TOKENS,
                    stream=True
                )
                
                full_response = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        if status_callback:
                            await status_callback('stream_chunk', {'content': content})
                
                if status_callback:
                    await status_callback('complete', {
                        'response': full_response,
                        'sources': [],
                        'tool_calls': [],
                        'notes': []
                    })
                    
        except Exception as e:
            print(f"Error in process_message_stream: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            if status_callback:
                await status_callback('error', {'error': str(e)})
            raise