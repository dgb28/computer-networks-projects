# 🌐 Web Cache Proxy Server (Python Sockets)

This project implements a **simple HTTP web cache proxy server** using **raw TCP sockets in Python**.  
The proxy sits between a client and an origin HTTP server, caching GET responses to improve performance and reduce redundant network traffic.

This project was completed as part of **CSCI-P538: Computer Networks (Project Assignment 2)**.

---

## 🎯 Project Objectives

- Implement an **HTTP proxy server** using TCP sockets
- Forward client requests to an origin server transparently
- Cache HTTP **GET** responses locally
- Enforce cache freshness using **TTL (Time-To-Live)**
- Apply **Least Recently Used (LRU)** cache replacement
- Validate correctness using `curl` and multi-VM testing

---

## 🧠 System Architecture

```
Client  →  Proxy Server  →  Origin HTTP Server
```

- **Client:** Sends HTTP requests using `curl`
- **Proxy Server:** Intercepts, forwards, and caches responses
- **Origin Server:** Simple HTTP server from Project 1

---

## ⚙️ Proxy Server Overview

- **Language:** Python  
- **Networking:** TCP sockets (`AF_INET`, `SOCK_STREAM`)  
- **Listening Address:** `0.0.0.0:8080`  
- **Cache Policy:** TTL + LRU  
- **Default Cache Size:** 10 objects  
- **Cache Storage:** Local filesystem (`./cache/`)  

The TTL value is provided as a command-line argument when starting the proxy.

```bash
python3 proxy.py <TTL>
```

Example:
```bash
python3 proxy.py 15
```

---

## 🔌 HTTP Request Handling

### ✅ GET Requests (Cached)

For every GET request, the proxy:

1. Checks if the requested resource exists in cache  
2. Validates freshness using TTL  
3. Returns cached response on a **cache hit**  
4. Fetches from origin server on a **cache miss or expiration**  
5. Stores the response and updates LRU ordering  

Proxy logs indicate cache behavior:
```
[PROXY] Cache HIT
[PROXY] Cache MISS
[PROXY] Cache EXPIRED
```

---

### 🚫 Non-GET Requests (Not Cached)

Requests such as:
- POST
- PUT
- HEAD

are forwarded directly to the origin server without caching.

```bash
curl -i -X POST -d "data=test" http://<PROXY_IP>:8080/post
```

---

## 🧠 TTL-Based Freshness

- Each cached object stores a timestamp
- On access:
  ```
  current_time - stored_time < TTL
  ```
- Expired objects are removed and re-fetched

This prevents serving stale content.

---

## ♻️ LRU Cache Replacement

- Implemented using an ordered in-memory structure
- Most recently accessed items move to the front
- When cache is full, least recently used item is evicted

Example eviction log:
```
[PROXY] Evicting /index.html
```

---

## 🧪 Testing & Validation

The proxy was tested using:
- `curl` from a client VM
- An origin server running Project 1

Verified scenarios:
- Cache miss followed by cache hit
- TTL-based cache expiration
- LRU eviction after cache limit
- Forwarding of non-GET requests
- Correct end-to-end client–proxy–server interaction

---

## 🔐 Robustness & Design Choices

- Uses `SO_REUSEADDR` for reliable restarts
- Stores cached responses on disk
- Maintains cache metadata in memory
- Gracefully handles malformed requests
- Separates proxy logic from origin server logic

---

## 📁 Repository Structure

```
.
├── proxy.py            # Web cache proxy implementation
├── server.py           # Origin HTTP server (from Project 1)
├── cache/              # Cached HTTP responses
├── PA2.pdf             # Assignment instructions
├── Project 2.pdf       # Project report
└── README.md
```

---

## 📌 Key Takeaways

- Built a functional **HTTP proxy cache from scratch**
- Implemented real-world caching concepts (TTL, LRU)
- Gained experience with:
  - Proxy-based architectures
  - Web performance optimization
  - Application-layer protocol design
- Strengthened understanding of HTTP transparency and caching

---

## 📚 Course Context

- **Course:** CSCI-P538 — Computer Networks  
- **Topics:** HTTP proxies, caching, TTL, LRU, socket programming
