"""
Web Research Framework v2 - Complete rewrite with Crawl4AI
Combines advanced web scraping with Cohere LLM integration
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy

from openai import OpenAI
import httpx

# Import configuration
from config import (
    OAUTH_CONFIG,
    SSL_CERT_PATH,
    MODEL_NAME,
    MAX_TOKENS,
    SERVER_HOST,
    SERVER_PORT,
    WS_RECONNECT_INTERVAL,
    MAX_SEARCH_RESULTS,
    MAX_CONTENT_LENGTH,
    REQUEST_TIMEOUT
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Web Research Framework v2")

# Request/Response models
class ResearchRequest(BaseModel):
    url: HttpUrl
    query: str
    extract_structured_data: bool = False
    extraction_schema: Optional[Dict[str, Any]] = None
    max_tokens: int = MAX_TOKENS

class ResearchResponse(BaseModel):
    url: str
    title: str
    content_summary: str
    llm_analysis: str
    extracted_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any]
    timestamp: str

class WebsocketMessage(BaseModel):
    type: str
    data: Any

# OAuth token management
class OAuthTokenManager:
    def __init__(self):
        self.token = None
        self.token_expiry = None
    
    async def get_token(self) -> str:
        """Get valid OAuth token, refreshing if needed"""
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token
        
        # Get new token
        async with httpx.AsyncClient(verify=SSL_CERT_PATH if os.path.exists(SSL_CERT_PATH) else True) as client:
            response = await client.post(
                OAUTH_CONFIG['oauth_url'],
                data={
                    'grant_type': 'client_credentials',
                    'client_id': OAUTH_CONFIG['client_id'],
                    'client_secret': OAUTH_CONFIG['client_secret'],
                },
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            self.token = data['access_token']
            # Assume 1 hour expiry if not provided
            expires_in = data.get('expires_in', 3600)
            self.token_expiry = datetime.now().timestamp() + expires_in - 60  # 1 minute buffer
            
            return self.token

# Initialize token manager
token_manager = OAuthTokenManager()

# Web scraping with Crawl4AI
class WebScraper:
    def __init__(self):
        self.browser_config = BrowserConfig(
            headless=True,
            java_script_enabled=True,
            extra_args=[
                '--ignore-certificate-errors',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
    
    async def scrape(self, url: str, extraction_schema: Optional[Dict] = None) -> Dict[str, Any]:
        """Scrape a URL and optionally extract structured data"""
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            # Configure extraction strategy if schema provided
            extraction_strategy = None
            if extraction_schema:
                extraction_strategy = JsonCssExtractionStrategy(extraction_schema)
            
            # Crawl configuration
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                wait_for="css:body",
                delay_before_return_html=2.0,
                extraction_strategy=extraction_strategy
            )
            
            # Perform crawl
            result = await crawler.arun(url=str(url), config=run_config)
            
            if not result.success:
                raise HTTPException(status_code=400, detail=f"Failed to scrape {url}")
            
            return {
                'markdown': result.markdown,
                'title': result.metadata.get('title', 'Untitled'),
                'extracted_content': json.loads(result.extracted_content) if result.extracted_content else None,
                'metadata': result.metadata,
                'html': result.html,
            }

# LLM integration
class LLMAnalyzer:
    def __init__(self):
        self.client = None
    
    async def initialize(self):
        """Initialize OpenAI client with OAuth token"""
        token = await token_manager.get_token()
        self.client = OpenAI(
            api_key=token,
            base_url=OAUTH_CONFIG['base_url'],
            http_client=httpx.Client(verify=SSL_CERT_PATH if os.path.exists(SSL_CERT_PATH) else True)
        )
    
    async def analyze(self, content: str, query: str, max_tokens: int = MAX_TOKENS) -> str:
        """Analyze scraped content with LLM"""
        if not self.client:
            await self.initialize()
        
        # Truncate content if too long
        if len(content) > MAX_CONTENT_LENGTH * 3:
            content = content[:MAX_CONTENT_LENGTH * 3] + "...[truncated]"
        
        messages = [
            {
                "role": "system",
                "content": "You are a helpful web research assistant. Analyze the provided web content and answer the user's query based on the information found."
            },
            {
                "role": "user",
                "content": f"Web Content:\n{content}\n\nQuery: {query}\n\nProvide a comprehensive answer based on the content above."
            }
        ]
        
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=MODEL_NAME,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return f"Analysis failed: {str(e)}"

# Import agent
from agent_v2 import ResearchAgentV2

# Initialize components
scraper = WebScraper()
analyzer = LLMAnalyzer()
agents = {}  # Store agent instances per session

# API Routes
@app.get("/")
async def root():
    """Serve the web interface"""
    with open("static/index_v3.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """Perform web research: scrape URL and analyze with LLM"""
    try:
        # Scrape the website
        logger.info(f"Scraping {request.url}")
        scrape_result = await scraper.scrape(
            request.url,
            request.extraction_schema
        )
        
        # Analyze with LLM
        logger.info(f"Analyzing content with LLM")
        analysis = await analyzer.analyze(
            scrape_result['markdown'],
            request.query,
            request.max_tokens
        )
        
        # Prepare response
        response = ResearchResponse(
            url=str(request.url),
            title=scrape_result['title'],
            content_summary=scrape_result['markdown'][:500] + "..." if len(scrape_result['markdown']) > 500 else scrape_result['markdown'],
            llm_analysis=analysis,
            extracted_data=scrape_result['extracted_content'],
            metadata=scrape_result['metadata'],
            timestamp=datetime.now().isoformat()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Research failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time research updates"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            # Handle different message formats
            if 'data' not in data:
                # Handle simple messages (like chat)
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Please use the research form to submit queries"}
                })
                continue
            
            message = WebsocketMessage(**data)
            
            if message.type == "chat":
                # Handle chat messages
                session_id = message.data.get('session_id', 'default')
                user_message = message.data.get('message', '')
                
                if not user_message:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": "Message is required"}
                    })
                    continue
                
                # Get or create agent
                if session_id not in agents:
                    token = await token_manager.get_token()
                    agents[session_id] = ResearchAgentV2(token)
                
                agent = agents[session_id]
                
                # Send status callback with streaming support
                async def status_callback(status: str):
                    if status.startswith("stream_chunk:"):
                        # Send streaming chunk
                        content = status[13:]  # Remove "stream_chunk:" prefix
                        await websocket.send_json({
                            "type": "stream_chunk",
                            "data": {"content": content}
                        })
                    else:
                        # Regular status message
                        await websocket.send_json({
                            "type": "status",
                            "data": {"message": status}
                        })
                
                # Process message
                result = await agent.process_message(user_message, status_callback)
                
                # Send response
                await websocket.send_json({
                    "type": "chat_response",
                    "data": {
                        'response': result.get('response', ''),
                        'sources': result.get('sources', []),
                        'notes_count': result.get('notes_count', 0),
                        'session_id': session_id
                    }
                })
                
            elif message.type == "research":
                # Send progress updates
                await websocket.send_json({
                    "type": "status",
                    "data": {"message": "Starting web scrape..."}
                })
                
                # Perform research
                request = ResearchRequest(**message.data)
                
                # Scrape
                await websocket.send_json({
                    "type": "status",
                    "data": {"message": f"Scraping {request.url}..."}
                })
                scrape_result = await scraper.scrape(request.url, request.extraction_schema)
                
                # Analyze
                await websocket.send_json({
                    "type": "status",
                    "data": {"message": "Analyzing with AI..."}
                })
                analysis = await analyzer.analyze(
                    scrape_result['markdown'],
                    request.query,
                    request.max_tokens
                )
                
                # Send result
                response = ResearchResponse(
                    url=str(request.url),
                    title=scrape_result['title'],
                    content_summary=scrape_result['markdown'][:500] + "...",
                    llm_analysis=analysis,
                    extracted_data=scrape_result['extracted_content'],
                    metadata=scrape_result['metadata'],
                    timestamp=datetime.now().isoformat()
                )
                
                await websocket.send_json({
                    "type": "result",
                    "data": response.dict()
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "data": {"message": str(e)}
        })

@app.post("/api/chat")
async def chat(request: Dict[str, Any]):
    """Chat with the research agent"""
    session_id = request.get('session_id', 'default')
    message = request.get('message', '')
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Get or create agent for this session
    if session_id not in agents:
        token = await token_manager.get_token()
        agents[session_id] = ResearchAgentV2(token)
    
    agent = agents[session_id]
    
    # Process message
    result = await agent.process_message(message)
    
    return {
        'success': result.get('success', False),
        'response': result.get('response', ''),
        'sources': result.get('sources', []),
        'notes_count': result.get('notes_count', 0),
        'session_id': session_id
    }

# Preview functionality removed - using simple new tab links instead

@app.get("/api/sources/{session_id}")
async def get_sources(session_id: str = 'default'):
    """Get all sources collected by the agent"""
    if session_id not in agents:
        return {'sources': {}}
    
    return {'sources': agents[session_id].get_all_sources()}

@app.get("/api/notes/{session_id}")
async def get_notes(session_id: str = 'default'):
    """Get all research notes"""
    if session_id not in agents:
        return {'notes': []}
    
    return {'notes': agents[session_id].get_all_notes()}

@app.post("/api/reset/{session_id}")
async def reset_conversation(session_id: str = 'default'):
    """Reset the conversation for a session"""
    if session_id in agents:
        result = agents[session_id].reset_conversation()
        return result
    return {'success': True, 'message': 'No active session'}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ssl_cert_exists": os.path.exists(SSL_CERT_PATH),
        "oauth_configured": bool(OAUTH_CONFIG['client_id'] != 'YOUR_CLIENT_ID_HERE'),
        "model": MODEL_NAME,
        "max_tokens": MAX_TOKENS
    }

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)