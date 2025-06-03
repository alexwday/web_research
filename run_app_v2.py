#!/usr/bin/env python3
"""
Run script for Web Research Framework v2
Sets up environment variables and starts the FastAPI server
"""

import os
import sys
import subprocess

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import crawl4ai
        import fastapi
        import openai
        import httpx
        import playwright
        print("✅ All Python requirements installed")
    except ImportError as e:
        print(f"❌ Missing requirement: {e}")
        print("Please run: pip install -r requirements.txt")
        if 'playwright' in str(e):
            print("Then run: playwright install chromium")
        sys.exit(1)

def check_configuration():
    """Check configuration file"""
    try:
        from config import OAUTH_CONFIG, SSL_CERT_PATH
        
        # Check if config has been updated from defaults
        if OAUTH_CONFIG['client_id'] == 'YOUR_CLIENT_ID_HERE':
            print("⚠️  Configuration not updated!")
            print("Please edit config.py and update:")
            print("  - oauth_url")
            print("  - client_id") 
            print("  - client_secret")
            print("  - base_url")
            return False
        
        print("✅ Configuration loaded from config.py")
        return True
    except ImportError as e:
        print(f"❌ Failed to import config.py: {e}")
        return False

def main():
    """Main entry point"""
    print("🚀 Starting Web Research Framework v2")
    
    # Check requirements
    check_requirements()
    
    # Check configuration
    if not check_configuration():
        sys.exit(1)
    
    # Check SSL certificate
    ssl_cert_path = os.path.join(os.path.dirname(__file__), 'ssl_certs', 'rbc-ca-bundle.cer')
    if os.path.exists(ssl_cert_path):
        print(f"✅ SSL certificate found: {ssl_cert_path}")
    else:
        print("⚠️  SSL certificate not found. HTTPS requests may fail in enterprise environments")
    
    # Start the application
    print("\n🌐 Starting FastAPI server on http://localhost:8000")
    print("Press CTRL+C to stop\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app_v2:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

if __name__ == "__main__":
    main()