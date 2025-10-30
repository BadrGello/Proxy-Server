#!/usr/bin/env python3
"""
Simple test client for the proxy server.
Run this after starting the proxy server.
"""

import socket
import sys

def test_proxy(proxy_host='localhost', proxy_port=8888, target_url='www.example.com'):
    """Send a GET request through the proxy."""
    try:
        # Create socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((proxy_host, proxy_port))
        
        # Create HTTP GET request
        request = f"GET http://{target_url}/ HTTP/1.0\r\n"
        request += f"Host: {target_url}\r\n"
        request += "\r\n"
        
        print(f"Sending request to proxy:\n{request}")
        
        # Send request
        client_socket.sendall(request.encode())
        
        # Receive response
        response = b""
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            response += data
        
        client_socket.close()
        
        # Print response
        print("\n----- Response from Proxy -----")
        print(response.decode('utf-8', errors='ignore')[:500])
        print("\n... (truncated)")
        print(f"\nTotal response size: {len(response)} bytes")
        
        return True
    
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "www.example.com"
    
    print(f"Testing proxy with target: {target}\n")
    test_proxy(target_url=target)
