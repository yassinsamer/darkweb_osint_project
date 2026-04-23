#!/usr/bin/env python3
"""
Quick test script to verify Tor is working
Run this to confirm your Tor SOCKS5 proxy is accessible
"""

import requests
import sys

TOR_PROXY = "socks5h://127.0.0.1:9150"

def test_tor_connection():
    """Test if Tor proxy is accessible"""
    print("[*] Testing Tor SOCKS5 proxy connection...")
    print(f"[*] Target: {TOR_PROXY}\n")
    
    try:
        session = requests.Session()
        session.proxies = {"http": TOR_PROXY, "https": TOR_PROXY}
        session.timeout = 30
        
        print("[+] Fetching IP info through Tor...")
        response = session.get("http://httpbin.org/ip", timeout=30)
        
        if response.status_code == 200:
            ip_data = response.json()
            print(f"[✓] SUCCESS! Your Tor exit IP: {ip_data['origin']}\n")
            print("[+] Tor is working correctly!")
            print("[+] You can now run the orchestrator with confidence")
            return True
        else:
            print(f"[!] Error: Got status code {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"[✗] FAILED: Cannot connect to Tor proxy")
        print(f"[!] Error: {e}\n")
        print("TROUBLESHOOTING:")
        print("1. Make sure Tor Browser is running")
        print("2. Check that SOCKS5 is enabled on port 9150")
        print("3. Verify firewall isn't blocking 127.0.0.1:9150")
        print("4. Try restarting Tor Browser")
        return False
        
    except requests.exceptions.Timeout:
        print(f"[✗] FAILED: Tor connection timed out (30s)")
        print("[!] This could mean Tor is slow or overloaded")
        return False
        
    except Exception as e:
        print(f"[✗] FAILED: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = test_tor_connection()
    sys.exit(0 if success else 1)
