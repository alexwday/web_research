from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import json
import os
from typing import Dict, Any
from agent import ResearchAgent
import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configuration
from config import OAUTH_CONFIG, SSL_CERT_PATH, SERVER_HOST, SERVER_PORT, MODEL_NAME

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance (in production, use proper session management)
agent = None

def get_agent():
    global agent
    if agent is None:
        try:
            logger.info("Initializing ResearchAgent...")
            agent = ResearchAgent(OAUTH_CONFIG, SSL_CERT_PATH)
            logger.info("ResearchAgent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ResearchAgent: {e}")
            raise
    return agent


@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, 'index.html'))


@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify configuration"""
    try:
        agent = get_agent()
        return {
            "status": "healthy",
            "model": MODEL_NAME,
            "ssl_cert_exists": os.path.exists(SSL_CERT_PATH),
            "config_loaded": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "model": MODEL_NAME,
            "ssl_cert_exists": os.path.exists(SSL_CERT_PATH)
        }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    agent = get_agent()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data['type'] == 'chat':
                # Process message with agent
                user_message = message_data['message']
                
                # Send thinking status
                await websocket.send_text(json.dumps({
                    'type': 'status',
                    'status': 'thinking'
                }))
                
                # Define callback for streaming
                async def status_callback(event_type, data):
                    if event_type == 'tool_use':
                        await websocket.send_text(json.dumps({
                            'type': 'tool_use',
                            'tool': data['tool'],
                            'arguments': data['arguments']
                        }))
                    elif event_type == 'stream_chunk':
                        await websocket.send_text(json.dumps({
                            'type': 'stream',
                            'content': data['content']
                        }))
                    elif event_type == 'complete':
                        await websocket.send_text(json.dumps({
                            'type': 'complete',
                            'data': data
                        }))
                    elif event_type == 'error':
                        await websocket.send_text(json.dumps({
                            'type': 'error',
                            'message': data['error']
                        }))
                
                try:
                    # Process message with streaming
                    await agent.process_message_stream(user_message, status_callback)
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send_text(json.dumps({
                        'type': 'error',
                        'message': str(e)
                    }))
            
            elif message_data['type'] == 'clear':
                agent.clear_session()
                await websocket.send_text(json.dumps({
                    'type': 'cleared',
                    'message': 'Session cleared'
                }))
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("WebSocket connection closed")


@app.get("/api/source/{url:path}")
async def get_source(url: str):
    """Get source content for viewing"""
    agent = get_agent()
    
    logger.info(f"Fetching source: {url}")
    
    # Always try to fetch fresh content
    try:
        result = agent.fetch_page_content(url)
        if result['success']:
            return {
                'url': url,
                'title': result.get('title', 'Unknown'),
                'content': result.get('content', 'No content available'),
                'timestamp': datetime.now().isoformat()
            }
        else:
            # If fetch failed, check if we have cached data
            if url in agent.sources:
                source_data = agent.sources[url]
                return {
                    'url': url,
                    'title': source_data.get('title', 'Unknown'),
                    'content': source_data.get('content', source_data.get('snippet', 'No content available')),
                    'timestamp': source_data.get('timestamp', datetime.now().isoformat())
                }
            else:
                logger.error(f"Failed to fetch source: {url} - {result.get('error', 'Unknown error')}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to fetch source: {result.get('error', 'Unknown error')}"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching source {url}: {e}")
        # Try to return cached data if available
        if url in agent.sources:
            source_data = agent.sources[url]
            return {
                'url': url,
                'title': source_data.get('title', 'Unknown'),
                'content': source_data.get('content', source_data.get('snippet', 'Error loading content')),
                'timestamp': source_data.get('timestamp', datetime.now().isoformat())
            }
        else:
            raise HTTPException(status_code=500, detail=f"Error fetching source: {str(e)}")


@app.get("/api/notes")
async def get_notes():
    """Get all research notes"""
    agent = get_agent()
    return {
        'notes': [note.to_dict() for note in agent.notes]
    }


# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Create static directory if it doesn't exist
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)