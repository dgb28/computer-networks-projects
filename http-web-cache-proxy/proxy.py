import socket
import os
import sys
import time
from collections import OrderedDict

# --- Configuration ---
# You can change these or pass them as arguments
PROXY_HOST = '0.0.0.0'
PROXY_PORT = 8080
CACHE_DIR = './cache'
MAX_CACHE_SIZE = 10
# SET THIS TO YOUR VM-SERVER IP ADDRESS
ORIGIN_SERVER_IP = '192.168.56.101'  
ORIGIN_SERVER_PORT = 8080

# Get TTL from command line or default to 10 seconds
TTL = int(sys.argv[1]) if len(sys.argv) > 1 else 10

# Ensure cache directory exists
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# --- LRU Cache Structure ---
# Maps path -> {'filename': str, 'timestamp': float}
cache_memory = OrderedDict()

def get_from_origin(method, path, headers, body=None):
    """
    Connects to the actual VM-Server to fetch/send data.
    Used for Cache Misses, Expirations, and Non-GET requests.
    """
    try:
        # 1. Create a socket to connect to the Origin Server
        origin_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        origin_sock.connect((ORIGIN_SERVER_IP, ORIGIN_SERVER_PORT))
        
        # 2. Reconstruct the HTTP request to send to Origin
        request_line = f"{method} {path} HTTP/1.1\r\n"
        
        # Forward necessary headers (Host is important)
        full_request = request_line + f"Host: {ORIGIN_SERVER_IP}:{ORIGIN_SERVER_PORT}\r\n"
        # Add other headers from the client if necessary, or just close connection
        full_request += "Connection: close\r\n\r\n"
        
        if body:
            full_request += body

        # 3. Send request and receive response
        origin_sock.sendall(full_request.encode())
        
        response_data = b""
        while True:
            chunk = origin_sock.recv(4096)
            if not chunk: break
            response_data += chunk
            
        origin_sock.close()
        return response_data
    except Exception as e:
        print(f"Error contacting origin: {e}")
        return None

def handle_client(client_socket):
    request_data = client_socket.recv(4096).decode('utf-8', errors='ignore')
    if not request_data:
        client_socket.close()
        return

    # 1. Parse the Request
    lines = request_data.split('\r\n')
    request_line = lines[0].split()
    if len(request_line) < 3: return
    method, path, version = request_line

    # --- HANDLE NON-GET REQUESTS [cite: 177] ---
    if method != 'GET':
        print(f"[PROXY] Forwarding {method} request directly to server.")
        # Extract body if POST/PUT
        body = request_data.split('\r\n\r\n')[1] if '\r\n\r\n' in request_data else None
        
        response = get_from_origin(method, path, {}, body)
        if response:
            client_socket.sendall(response)
        client_socket.close()
        return

    # --- HANDLE GET REQUESTS (Caching Logic) ---
    
    # 2. Check Cache Hit/Miss
    current_time = time.time()
    is_cached = path in cache_memory
    
    response_content = None

    if is_cached:
        # Check Freshness (TTL) 
        entry = cache_memory[path]
        age = current_time - entry['timestamp']
        
        if age < TTL:
            print(f"[PROXY] Cache HIT for {path}")
            # Update LRU position [cite: 172]
            cache_memory.move_to_end(path)
            
            # Load from disk 
            with open(os.path.join(CACHE_DIR, entry['filename']), 'rb') as f:
                response_content = f.read()
        else:
            print(f"[PROXY] Cache EXPIRED for {path}")
            # Treat as miss (fall through to origin fetch)
    else:
        print(f"[PROXY] Cache MISS for {path}")

    # 3. Fetch from Origin if no valid cache
    if response_content is None:
        raw_response = get_from_origin("GET", path, {})
        
        if raw_response:
            # We need to parse headers to check for "200 OK" before caching [cite: 158]
            header_part = raw_response.split(b'\r\n\r\n')[0].decode(errors='ignore')
            
            if "200 OK" in header_part:
                # --- SAVE TO CACHE ---
                filename = path.strip('/').replace('/', '_') or 'index.html'
                filepath = os.path.join(CACHE_DIR, filename)
                
                # Write to disk
                with open(filepath, 'wb') as f:
                    f.write(raw_response)
                
                # Update Memory Dict
                if len(cache_memory) >= MAX_CACHE_SIZE:
                    # Evict LRU (first item) [cite: 171, 175]
                    evicted = cache_memory.popitem(last=False)
                    print(f"[PROXY] Evicting {evicted[0]}")
                    # Optional: Delete the actual file from disk to save space
                
                # Add new entry to end (MRU) [cite: 173]
                cache_memory[path] = {'filename': filename, 'timestamp': time.time()}
            
            response_content = raw_response

    # 4. Send Response to Client
    if response_content:
        client_socket.sendall(response_content)
    
    client_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((PROXY_HOST, PROXY_PORT))
    server_socket.listen(5)
    print(f"Proxy listening on {PROXY_HOST}:{PROXY_PORT} with TTL={TTL}")

    while True:
        try:
            client_sock, addr = server_socket.accept()
            handle_client(client_sock)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()