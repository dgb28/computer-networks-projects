# 🌐 Simple HTTP Server (Python Sockets)

This project implements a **simple HTTP/1.1 server from scratch in Python** using **raw TCP sockets**.  
The server supports multiple HTTP methods and demonstrates a practical understanding of **network protocols, socket programming, and HTTP request/response handling**.

This project was completed as part of **CSCI-P538: Computer Networks (Project Assignment 1)**.

---

## 🎯 Project Objectives

- Understand the **structure of HTTP/1.1 messages**
- Implement a **TCP-based HTTP server** using Python sockets
- Correctly parse HTTP requests (request line, headers, body)
- Support core HTTP methods: **GET, POST, PUT, HEAD**
- Test and validate server behavior using **curl** and a web browser

---

## 🧠 Server Overview

- **Language:** Python  
- **Networking:** TCP sockets (`AF_INET`, `SOCK_STREAM`)  
- **Listening Address:** `0.0.0.0:8080`  
- **HTTP Version:** HTTP/1.1  
- **Server Root Directory:**
  ```
  ~/simple_http/www/
  ```

The server manually constructs HTTP responses and does **not** rely on any web frameworks.

---

## 🔌 Supported HTTP Methods

### ✅ GET
- Retrieves files from the server root directory
- Default path (`/`) maps to:
  ```
  ~/simple_http/www/index.html
  ```
- Returns:
  - `200 OK` if the file exists
  - `404 Not Found` if the file is missing

```bash
curl -i http://<SERVER_IP>:8080/
```

---

### ✅ POST
- Allowed **only** at the endpoint `/post`
- Appends request body data to:
  ```
  ~/simple_http/post_data.txt
  ```
- Returns `200 OK` upon successful write

```bash
curl -i -X POST -d "student=test&msg=hello" http://<SERVER_IP>:8080/post
```

---

### ✅ PUT
- Creates or overwrites files on the server
- Writes request body to a file under:
  ```
  ~/simple_http/www/
  ```
- Returns:
  - `201 Created` if the file is newly created
  - `200 OK` if the file already exists

```bash
curl -i -X PUT -d "sample text" http://<SERVER_IP>:8080/upload/foo.txt
```

---

### ✅ HEAD
- Same behavior as `GET` but **without a response body**
- Returns headers only, including:
  - `Content-Type`
  - `Content-Length`

```bash
curl -I http://<SERVER_IP>:8080/index.html
```

---

### ❌ Unsupported Methods
Methods such as `DELETE` return:
```http
HTTP/1.1 405 Method Not Allowed
Allow: GET, POST, PUT, HEAD
```

---

## 🧪 Testing & Validation

The server was tested using:
- `curl` for command-line HTTP requests
- A web browser for manual GET requests

Verified test cases include:
- File retrieval using GET
- POST data persistence
- PUT file creation and overwrite
- HEAD header-only responses
- Proper handling of unsupported methods

---

## 🔐 Security & Robustness

- Prevents directory traversal (`..`)
- Restricts POST to a single endpoint
- Handles malformed requests gracefully
- Uses `SO_REUSEADDR` for reliable restarts
- Closes connections after each response

---

## 📌 Key Takeaways

- Implemented an HTTP server **without using frameworks**
- Gained hands-on experience with:
  - TCP socket programming
  - HTTP protocol internals
  - Client–server communication
- Learned how to test network services using real clients

---

## 📚 Course Context

- **Course:** CSCI-P538 — Computer Networks  
- **Topics:** HTTP, TCP, sockets, application-layer protocols
