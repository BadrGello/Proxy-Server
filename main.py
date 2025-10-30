from socket import *
import sys
import os


if len(sys.argv) <= 1:
    print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server]')
    sys.exit(2)

server_ip = sys.argv[1]
server_port = 8888   

tcpSerSock = socket(AF_INET, SOCK_STREAM)
tcpSerSock.bind((server_ip, server_port))
tcpSerSock.listen(5)
print(f"Proxy Server running on {server_ip}:{server_port}\n")

while True:
    print('Ready to serve...')
    tcpCliSock, addr = tcpSerSock.accept()
    print('Received a connection from:', addr)

    try:
        # Receive client request
        message = tcpCliSock.recv(4096).decode()
        if not message:
            tcpCliSock.close()
            continue

        print(f"\n----- Client Request -----\n{message}\n---------------------------")

        # Extract method and filename
        request_parts = message.split()
        if len(request_parts) < 2:
            tcpCliSock.close()
            continue

        method = request_parts[0]  # request type
        full_url = request_parts[1]  # e.g., "http://www.google.com/index.html" or "/www.google.com/index.html"
        
        # Remove http:// prefix if present
        if full_url.startswith("http://"):
            full_url = full_url[7:]
        elif full_url.startswith("/"):
            full_url = full_url[1:]
        
        filename = full_url  # e.g., "www.google.com/index.html"
        fileExist = False
        
        # Create a safe cache filename
        file_to_use = filename.replace("/", "_").replace(":", "_")
        if not file_to_use:
            file_to_use = "index_cache"


        if os.path.isfile(file_to_use):
            print("Cache hit. Serving from cache...")
            fileExist = True
            with open(file_to_use, "rb") as f:
                cached_data = f.read()

            # Send cached response
            tcpCliSock.send(b"HTTP/1.0 200 OK\r\n")
            tcpCliSock.send(b"Content-Type: text/html\r\n\r\n")
            tcpCliSock.send(cached_data)
            print("Served from cache.\n")

        # ----------------------------
        # 5. Cache miss → fetch from server
        # ----------------------------
        else:
            print("Cache miss. Fetching from remote server...")

            # Extract hostname and path correctly
            url_parts = filename.split("/", 1)
            hostn = url_parts[0]               # e.g., "www.google.com"
            path = "/" + url_parts[1] if len(url_parts) > 1 else "/"  # e.g., "/index.html"

            print(f"Connecting to host: {hostn}, path: {path}")


            try:
                # Create connection to remote web server
                c = socket(AF_INET, SOCK_STREAM)
                c.connect((hostn, 80))

                # Handle GET or POST request
                if method == "GET":
                    request_line = f"GET {path} HTTP/1.0\r\nHost: {hostn}\r\n\r\n"
                    c.sendall(request_line.encode())

                elif method == "POST":
                    # Extract POST body (if any)
                    headers, _, body = message.partition("\r\n\r\n")
                    request_line = f"POST {path} HTTP/1.0\r\nHost: {hostn}\r\n"
                    c.sendall((request_line + headers + "\r\n\r\n" + body).encode())

                response = b""
                while True:
                    data = c.recv(4096)
                    if not data:
                        break
                    response += data

                # Send response back to client
                tcpCliSock.sendall(response)
                print(f"Sent {len(response)} bytes to client")

                # Cache only GET responses
                if method == "GET" and response:
                    # Split response to check status code
                    try:
                        response_str = response.decode('utf-8', errors='ignore')
                        if '200 OK' in response_str.split('\r\n')[0]:
                            with open(file_to_use, "wb") as tmpFile:
                                tmpFile.write(response)
                            print(f"Response cached as: {file_to_use}\n")
                        else:
                            print("Not caching non-200 response\n")
                    except:
                        print("Could not cache response\n")

                c.close()

            except Exception as e:
                print(f"Error fetching from server: {e}")
                error_response = b"HTTP/1.0 502 Bad Gateway\r\n"
                error_response += b"Content-Type: text/html\r\n\r\n"
                error_response += b"<html><body><h1>502 Bad Gateway</h1>"
                error_response += f"<p>Error: {str(e)}</p></body></html>".encode()
                tcpCliSock.sendall(error_response)

    except Exception as e:
        print("Error processing client request:", e)

    tcpCliSock.close()
