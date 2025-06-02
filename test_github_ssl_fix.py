#!/usr/bin/env python3
"""
GitHub SSL Fix Test
Tests different approaches to fix the GitHub SSL certificate issue.
"""

import os
import requests
import ssl
import logging
from pathlib import Path

# Set up simple logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def setup_ssl():
    """Setup SSL certificate."""
    script_dir = Path(__file__).parent
    cert_path = script_dir / "ssl_certs" / "rbc-ca-bundle.cer"
    
    if cert_path.exists():
        logger.info(f"Using SSL certificate: {cert_path}")
        os.environ["SSL_CERT_FILE"] = str(cert_path)
        os.environ["REQUESTS_CA_BUNDLE"] = str(cert_path)
        return str(cert_path)
    else:
        logger.info("No SSL certificate found")
        return None

def test_github_approaches():
    """Test different approaches to connect to GitHub."""
    github_url = "https://github.com"
    results = {}
    
    print("Testing different GitHub SSL approaches...")
    print("-" * 50)
    
    # Approach 1: Default requests
    try:
        logger.info("1. Testing default requests...")
        response = requests.get(github_url, timeout=10)
        if response.status_code == 200:
            results["default"] = "SUCCESS"
            logger.info("   ✓ Default requests works!")
        else:
            results["default"] = f"HTTP {response.status_code}"
            logger.info(f"   ! Unexpected status: {response.status_code}")
    except Exception as e:
        results["default"] = f"Failed: {e}"
        logger.error(f"   ✗ Default requests failed: {e}")
    
    # Approach 2: Custom SSL context with less strict verification
    try:
        logger.info("2. Testing with custom SSL context...")
        session = requests.Session()
        session.mount('https://', requests.adapters.HTTPAdapter())
        
        # Create a more permissive SSL context
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # This approach uses requests built-in verification but with custom cert
        cert_path = setup_ssl()
        if cert_path:
            session.verify = cert_path
        
        response = session.get(github_url, timeout=10)
        if response.status_code == 200:
            results["custom_context"] = "SUCCESS"
            logger.info("   ✓ Custom SSL context works!")
        else:
            results["custom_context"] = f"HTTP {response.status_code}"
            logger.info(f"   ! Unexpected status: {response.status_code}")
    except Exception as e:
        results["custom_context"] = f"Failed: {e}"
        logger.error(f"   ✗ Custom SSL context failed: {e}")
    
    # Approach 3: Try with system CA bundle + custom cert
    try:
        logger.info("3. Testing with combined certificates...")
        import tempfile
        import shutil
        
        cert_path = setup_ssl()
        if cert_path:
            # Create a temporary combined cert file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as temp_cert:
                # First add system certs
                try:
                    with open('/etc/ssl/certs/ca-certificates.crt', 'r') as sys_certs:
                        temp_cert.write(sys_certs.read())
                except:
                    try:
                        with open('/usr/local/etc/openssl/cert.pem', 'r') as sys_certs:
                            temp_cert.write(sys_certs.read())
                    except:
                        pass  # No system certs found
                
                # Then add our custom cert
                with open(cert_path, 'r') as custom_cert:
                    temp_cert.write('\n')
                    temp_cert.write(custom_cert.read())
                
                temp_cert_path = temp_cert.name
            
            response = requests.get(github_url, verify=temp_cert_path, timeout=10)
            os.unlink(temp_cert_path)  # Clean up
            
            if response.status_code == 200:
                results["combined_certs"] = "SUCCESS"
                logger.info("   ✓ Combined certificates work!")
            else:
                results["combined_certs"] = f"HTTP {response.status_code}"
                logger.info(f"   ! Unexpected status: {response.status_code}")
        else:
            results["combined_certs"] = "No custom cert to combine"
            logger.info("   ! No custom certificate found")
            
    except Exception as e:
        results["combined_certs"] = f"Failed: {e}"
        logger.error(f"   ✗ Combined certificates failed: {e}")
    
    # Approach 4: Try different GitHub endpoints
    github_endpoints = [
        "https://api.github.com",
        "https://raw.githubusercontent.com",
        "https://github.com/robots.txt"
    ]
    
    logger.info("4. Testing different GitHub endpoints...")
    endpoint_results = {}
    for endpoint in github_endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            if response.status_code == 200:
                endpoint_results[endpoint] = "SUCCESS"
                logger.info(f"   ✓ {endpoint} works!")
            else:
                endpoint_results[endpoint] = f"HTTP {response.status_code}"
                logger.info(f"   ! {endpoint}: {response.status_code}")
        except Exception as e:
            endpoint_results[endpoint] = f"Failed: {e}"
            logger.error(f"   ✗ {endpoint} failed: {e}")
    
    results["endpoints"] = endpoint_results
    
    # Approach 5: Use urllib3 directly with custom SSL
    try:
        logger.info("5. Testing with urllib3 directly...")
        import urllib3
        
        # Disable SSL warnings for this test
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        http = urllib3.PoolManager(
            cert_reqs='CERT_NONE',
            assert_hostname=False
        )
        
        resp = http.request('GET', github_url)
        if resp.status == 200:
            results["urllib3"] = "SUCCESS"
            logger.info("   ✓ urllib3 direct works!")
        else:
            results["urllib3"] = f"HTTP {resp.status}"
            logger.info(f"   ! urllib3 status: {resp.status}")
            
    except Exception as e:
        results["urllib3"] = f"Failed: {e}"
        logger.error(f"   ✗ urllib3 failed: {e}")
    
    return results

def main():
    print("=" * 60)
    print("GITHUB SSL FIX TEST")
    print("=" * 60)
    
    setup_ssl()
    results = test_github_approaches()
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    working_approaches = []
    
    for approach, result in results.items():
        if approach == "endpoints":
            print(f"\nGitHub Endpoints:")
            for endpoint, endpoint_result in result.items():
                status = "✓" if "SUCCESS" in endpoint_result else "✗"
                print(f"  {status} {endpoint}: {endpoint_result}")
                if "SUCCESS" in endpoint_result:
                    working_approaches.append(f"endpoint_{endpoint}")
        else:
            status = "✓" if "SUCCESS" in result else "✗"
            print(f"{status} {approach}: {result}")
            if "SUCCESS" in result:
                working_approaches.append(approach)
    
    print(f"\nWorking approaches: {len(working_approaches)}")
    
    if working_approaches:
        print("\n🎉 Found working solutions for GitHub!")
        print("We can implement the best working approach in the web research framework.")
    else:
        print("\n⚠️  No approaches worked for GitHub.")
        print("GitHub might be completely blocked, but other sites work fine.")
        print("Web research can still work with other sources.")

if __name__ == "__main__":
    main()