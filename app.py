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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configuration
from config import OAUTH_CONFIG, SSL_CERT_PATH, SERVER_HOST, SERVER_PORT

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
        agent = ResearchAgent(OAUTH_CONFIG, SSL_CERT_PATH)
    return agent


@app.get("/")
async def root():
    return FileResponse('static/index.html')


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
                
                try:
                    # Process message (this is blocking, in production use background task)
                    result = agent.process_message(user_message)
                    
                    # Send response
                    await websocket.send_text(json.dumps({
                        'type': 'response',
                        'data': result
                    }))
                    
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
    
    if url in agent.sources:
        source_data = agent.sources[url]
        
        # If we don't have full content, fetch it
        if 'content' not in source_data:
            result = agent.fetch_page_content(url)
            if result['success']:
                source_data = agent.sources[url]
        
        return {
            'url': url,
            'title': source_data.get('title', 'Unknown'),
            'content': source_data.get('content', source_data.get('snippet', '')),
            'timestamp': source_data.get('timestamp')
        }
    else:
        # Try to fetch it
        result = agent.fetch_page_content(url)
        if result['success']:
            return {
                'url': url,
                'title': result['title'],
                'content': result['content'],
                'timestamp': agent.sources[url]['timestamp']
            }
        else:
            raise HTTPException(status_code=404, detail="Source not found")


@app.get("/api/notes")
async def get_notes():
    """Get all research notes"""
    agent = get_agent()
    return {
        'notes': [note.to_dict() for note in agent.notes]
    }


# Create static directory if it doesn't exist
os.makedirs('static', exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)