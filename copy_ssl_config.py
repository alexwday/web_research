#!/usr/bin/env python3
"""
SSL Configuration Copy Utility
Copies SSL configuration from cohere_testing to web_research project
"""

import os
import sys
import shutil
from pathlib import Path

def find_cohere_ssl_config():
    """Find the SSL configuration in cohere_testing project."""
    # Look for cohere_testing in common locations
    search_paths = [
        "/Users/alexwday/Projects/cohere_testing",
        "../cohere_testing",
        "../../cohere_testing"
    ]
    
    for path in search_paths:
        ssl_settings_path = Path(path) / "cohere" / "src" / "initial_setup" / "ssl" / "ssl_settings.py"
        if ssl_settings_path.exists():
            return ssl_settings_path.parent
    
    return None

def read_ssl_settings(ssl_dir):
    """Read SSL settings from cohere_testing."""
    settings_file = ssl_dir / "ssl_settings.py"
    
    if not settings_file.exists():
        return None
    
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Extract SSL_CERT_PATH if it's configured
    ssl_cert_path = None
    for line in content.split('\n'):
        if 'SSL_CERT_DIR' in line and not line.strip().startswith('#'):
            # Extract the directory path
            if '"' in line:
                ssl_cert_dir = line.split('"')[1]
                if ssl_cert_dir != "/path/to/certificates":  # Not the placeholder
                    ssl_cert_path = ssl_cert_dir
                    break
    
    return ssl_cert_path

def main():
    print("SSL Configuration Copy Utility")
    print("=" * 40)
    
    # Find cohere SSL configuration
    ssl_dir = find_cohere_ssl_config()
    if not ssl_dir:
        print("❌ Could not find cohere_testing SSL configuration")
        print("\nManual setup required:")
        print("1. Find your SSL certificate location")
        print("2. Set environment variable: export SSL_CERT_FILE=/path/to/your/cert.pem")
        print("3. Run: python test_web_scraper_ssl.py")
        return
    
    print(f"✓ Found SSL configuration at: {ssl_dir}")
    
    # Read SSL settings
    ssl_cert_path = read_ssl_settings(ssl_dir)
    
    if ssl_cert_path and ssl_cert_path != "/path/to/certificates":
        print(f"✓ Found SSL certificate path: {ssl_cert_path}")
        
        # Set environment variable
        os.environ["SSL_CERT_FILE"] = ssl_cert_path
        print(f"✓ Set SSL_CERT_FILE environment variable")
        
        print("\nTo make this permanent, add to your shell profile:")
        print(f"export SSL_CERT_FILE={ssl_cert_path}")
        
    else:
        print("⚠️  SSL certificate path not configured in cohere_testing")
        print("The SSL settings file contains placeholder values")
    
    print(f"\nNow run: python test_web_scraper_ssl.py")

if __name__ == "__main__":
    main()