import socket
import os
import sys

# --- Configuration ---
SERVER_DIR = os.path.join(os.path.expanduser('~'), 'simple_http', 'www')
POST_FILE_PATH = os.path.join(os.path.expanduser('~'), 'simple_http', 'post_data.txt')
HOST = '0.0.0.0'
PORT = 8080
HTTP_VERSION = 'HTTP/1.1'
ALLOWED_METHODS = ["GET", "POST", "PUT", "HEAD"]
# --- End Configuration ---

# --- Helper Functions for Response Formatting ---

def send_http_response(client_socket, code, message, headers, body=None):
    """Generates and sends an HTTP response."""
    response = f"{HTTP_VERSION} {code} {message}\r\n"
    if body and 'Content-Length' not in headers:
        headers['Content-Length'] = str(len(body.encode('utf-8')))
    
    # Adding headers to the response
    for key, value in headers.items():
        response += f"{key}: {value}\r\n"
    
    response += "Connection: close\r\n\r\n"
    
    # If there's a body, append it to the response
    if body:
        response += body

    # Send the full HTTP response
    client_socket.sendall(response.encode('utf-8'))

def send_error_response(client_socket, code, message, body=None):
    """Generates a standard error response like 404 or 500."""
    if not body:
        body = f"{code} {message}"
    headers = {'Content-Type': 'text/html'}
    send_http_response(client_socket, code, message, headers, body)

def send_method_not_allowed(client_socket):
    """Generates a 405 Method Not Allowed response."""
    allowed_methods = ', '.join(ALLOWED_METHODS)
    body = "Method Not Allowed"
    headers = {
        'Content-Type': 'text/plain',
        'Allow': allowed_methods 
    }
    send_http_response(client_socket, 405, "Method Not Allowed", headers, body)

# --- Path Handling ---

def resolve_file_path(path):
    """Resolves URL path to the file path in the server directory."""
    if path == '/' or path == '/index.html': 
        return os.path.join(SERVER_DIR, 'index.html')
    
    relative_path = path.lstrip('/')
    if '..' in relative_path:
        return None  # Prevent directory traversal
    
    return os.path.join(SERVER_DIR, relative_path)

# --- Method Handlers ---

def handle_get_request(client_socket, path):
    """Handles GET requests: returns the requested file or 404."""
    file_path = resolve_file_path(path)
    
    if file_path is None or not os.path.exists(file_path) or os.path.isdir(file_path):
        send_error_response(client_socket, 404, "Not Found", "404 Not Found")
        return
    
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        content_type = 'text/html' if file_path.endswith('.html') else 'text/plain'
        headers = {'Content-Type': content_type}
        
        send_http_response(client_socket, 200, "OK", headers, content)
    
    except Exception:
        send_error_response(client_socket, 500, "Internal Server Error")

def handle_head_request(client_socket, path):
    """Handles HEAD requests: similar to GET, but no body is returned."""
    file_path = resolve_file_path(path)
    
    if file_path is None or not os.path.exists(file_path) or os.path.isdir(file_path):
        send_error_response(client_socket, 404, "Not Found", "404 Not Found")
        return
    
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        content_type = 'text/html' if file_path.endswith('.html') else 'text/plain'
        content_length = str(len(content.encode('utf-8')))
        
        headers = {
            'Content-Type': content_type,
            'Content-Length': content_length
        }
        
        send_http_response(client_socket, 200, "OK", headers, body=None)
    
    except Exception:
        send_error_response(client_socket, 500, "Internal Server Error")

def handle_post_request(client_socket, path, body):
    """Handles POST requests: stores the body in post_data.txt at /post."""
    if path != '/post':
        send_error_response(client_socket, 403, "Forbidden", "POST only allowed at /post") 
        return
    
    try:
        with open(POST_FILE_PATH, 'a') as file: 
            file.write(body + '\n')
        
        response_body = "POST received and stored."
        headers = {'Content-Type': 'text/plain'}
        send_http_response(client_socket, 200, "OK", headers, response_body)
    
    except Exception:
        send_error_response(client_socket, 500, "Internal Server Error")

def handle_put_request(client_socket, path, body):
    """Handles PUT requests: writes the body to a specified file."""
    target_path = resolve_file_path(path)
    
    if target_path is None:
        send_error_response(client_socket, 403, "Forbidden", "Invalid path.")
        return
    
    is_new_file = not os.path.exists(target_path)

    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        with open(target_path, 'w') as file:
            file.write(body)
        
        if is_new_file:
            status_code, status_message = 201, "Created"
            response_body = f"PUT stored as {os.path.basename(target_path)}"
            headers = {'Content-Type': 'text/plain', 'Location': path}
        else:
            status_code, status_message = 200, "OK"
            response_body = f"PUT updated {os.path.basename(target_path)}"
            headers = {'Content-Type': 'text/plain'}
        
        send_http_response(client_socket, status_code, status_message, headers, response_body)
    
    except Exception:
        send_error_response(client_socket, 500, "Internal Server Error")

# --- Request Processing ---

def process_request(client_socket):
    """Reads, parses, and processes incoming HTTP requests."""
    request_data = client_socket.recv(4096).decode('utf-8')
    if not request_data:
        return
    
    lines = request_data.split('\r\n')
    request_line = lines[0]
    
    try:
        method, path, version = request_line.split()
    except ValueError:
        send_error_response(client_socket, 400, "Bad Request")
        client_socket.close()
        return
    
    headers = {}
    body_raw = request_data.split('\r\n\r\n', 1)
    header_lines = lines[1:]
    
    for line in header_lines:
        if line == '':
            break 
        try:
            name, value = line.split(': ', 1)
            headers[name.lower()] = value
        except ValueError:
            continue
    
    body = body_raw[1] if len(body_raw) > 1 else ""
    
    if method in ["POST", "PUT"]:
        content_length = int(headers.get('content-length', 0))
        if content_length != len(body.encode('utf-8')):
            print(f"Warning: Content-Length mismatch with body size.")

    if method not in ALLOWED_METHODS:
        send_method_not_allowed(client_socket) 
    elif method == "GET":
        handle_get_request(client_socket, path)
    elif method == "HEAD":
        handle_head_request(client_socket, path)
    elif method == "POST":
        handle_post_request(client_socket, path, body)
    elif method == "PUT":
        handle_put_request(client_socket, path, body)
    
    client_socket.close()

def main():
    """Main server loop to accept and handle requests."""
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"Server running on {HOST}:{PORT} with document root {SERVER_DIR}...")
    except Exception as e:
        print(f"Error setting up server: {e}")
        sys.exit(1)

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"Connection from {client_address[0]}:{client_address[1]}...")
            process_request(client_socket)
        except KeyboardInterrupt:
            print("\nServer shutting down gracefully...")
            server_socket.close()
            break
        except Exception as e:
            print(f"Error during request handling: {e}")
            continue

if __name__ == "__main__":
    main()
