# Cloud File Converter (Production-Grade SaaS)

<div align="center">

![Cloud File Converter Version](https://img.shields.io/badge/Version-1.1.0-6366f1?style=for-the-badge&logo=files&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python)
![Django](https://img.shields.io/badge/Django-5.x-092E20?style=flat-square&logo=django)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?style=flat-square&logo=typescript)
![PWA](https://img.shields.io/badge/PWA-Supported-00c7b7?style=flat-square&logo=progressive-web-apps)

**A 100% Free, High-Performance, Cloud-Native File Conversion & Processing Platform.**

Convert documents, images, and archives, extract text with OCR, and summarize files with AI — instantly in the cloud.

</div>

---

## 🏗️ Architecture Diagrams

### A. System Architecture
Comprehensive view of system boundary connections, showing secure ingress, ASGI/WSGI backend separation, task priority queues, and backing storage.

```mermaid
graph TB
    subgraph "Frontend Client — PWA"
        FE["React + Vite + TS (PWA)"]
        WS_Client["WebSocket Client"]
    end

    subgraph "Ingress & Gateway"
        CF["Cloudflare CDN (DDOS / Rate Limits)"]
        NG["Nginx (Reverse Proxy & Upstream SSL)"]
    end

    subgraph "Backend Servers"
        DJ["Django REST (WSGI - HTTP)"]
        CH["Django Channels (ASGI - WebSockets)"]
    end

    subgraph "Task Scheduling & Message Broker"
        RD["Redis (Task Broker & Channel Layer)"]
        Celery_Default["Celery Worker (Default Queue)"]
        Celery_Heavy["Celery Worker (OCR & AI Queue)"]
        Celery_Clean["Celery Worker (Cleanup Beat Queue)"]
    end

    subgraph "Data & Storage Layers"
        PG["PostgreSQL (User metadata & History)"]
        S3["AWS S3 / MinIO (Temporary Files)"]
    end

    CF --> NG
    NG --> DJ
    NG --> CH
    CH --> RD
    DJ --> PG
    DJ --> RD
    DJ --> S3
    Celery_Default --> PG
    Celery_Default --> S3
    Celery_Heavy --> S3
    Celery_Clean --> S3
```

---

### B. Database ER Diagram
Shows relation mappings, Compound Indexes (optimized for prunes), and guest-specific schema customizations (email and password nullability).

```mermaid
erDiagram
    USERS ||--o{ FILES : uploads
    USERS ||--o{ CONVERSIONS : initiates
    USERS ||--o{ AUDIT_LOGS : generates
    FILES ||--o{ CONVERSIONS : "source file"
    CONVERSIONS ||--o{ DOWNLOAD_SHARES : "has shareable links"

    USERS {
        uuid id PK
        string email UK "Nullable for Guests"
        string password_hash "Nullable for Guests"
        boolean is_guest
        timestamp last_activity
        bigint storage_used
        bigint storage_limit
        timestamp created_at
    }

    FILES {
        uuid id PK
        uuid user_id FK
        string original_name
        string stored_name
        string s3_key
        string mime_type
        string file_extension
        bigint file_size
        string status
        timestamp expires_at "Indexed for cleanup"
        timestamp created_at
    }

    CONVERSIONS {
        uuid id PK
        uuid user_id FK
        uuid source_file_id FK
        string conversion_type
        string source_format
        string target_format
        string status
        string output_s3_key
        boolean is_batch
        uuid batch_id "Indexed"
        float processing_time
        timestamp created_at
    }

    DOWNLOAD_SHARES {
        uuid id PK
        uuid conversion_id FK
        string share_token UK "Indexed"
        timestamp expires_at
        int download_count
        timestamp created_at
    }
```

---

### C. Conversion Workflow Diagram
Demonstrates how uploads map to async processing jobs, WebSocket streams, and secure file delivery.

```mermaid
sequenceDiagram
    autonumber
    actor User as Client PWA
    participant API as Django REST (HTTP)
    participant Broker as Redis (Broker)
    participant Worker as Celery Worker
    participant WS as Django Channels (WS)
    participant Storage as AWS S3 / MinIO

    User->>API: Upload File (Multipart Form)
    API->>Storage: Save Original File
    API->>API: Save File Record (DB)
    API->>Broker: Queue Conversion Job (Type)
    API-->>User: HTTP 201 (Created, Pending Status)
    
    Broker->>Worker: Consume Job
    Worker->>Storage: Download Original Bytes
    Worker->>Worker: Process (Conversion / OCR / AI)
    Worker->>Storage: Upload Converted Output
    Worker->>Broker: Broadcast "COMPLETED" Event
    
    Broker->>WS: Forward Event
    WS-->>User: WebSocket Stream (Progress / Completed)
    User->>API: Download File (Request)
    API->>Storage: Generate Pre-Signed Expirable URL
    API-->>User: Redirect to Download URL
```

---

### D. Deployment Architecture
High-availability infrastructure configurations for AWS environments.

```mermaid
graph LR
    User["User Browser"] --> CF["Cloudflare CDN"]
    CF --> CF_Edge["CloudFront Edge Cache"]
    CF_Edge --> ALB["Application Load Balancer"]
    ALB --> EC2["EC2 instance (App Server)"]
    
    subgraph "EC2 Server Daemons"
        NGX["Nginx Web Server"] --> GUNI["Gunicorn (WSGI - API)"]
        NGX --> DAPH["Daphne (ASGI - WS)"]
        CEL_DEF["Celery Worker (Default)"]
        CEL_HVY["Celery Worker (Heavy)"]
    end
    
    GUNI --> RDS["RDS PostgreSQL (DB)"]
    CEL_DEF --> RDS
    DAPH --> RED["ElastiCache Redis"]
    CEL_DEF --> RED
    CEL_HVY --> RED
    CEL_DEF --> S3["AWS S3 Bucket"]
    CEL_HVY --> S3
```

---

## ✨ Feature Showcase

### 1. Seamless Guest Mode
- **Zero Registration**: Drag-and-drop files to convert immediately.
- **Auto-Provisioning**: Creates a temporary guest profile and provides JWT tokens seamlessly in the background.

### 2. High-Performance Batch Processing
- **Checklist Workflow**: Upload up to 10 files simultaneously and pick custom target formats per file.
- **Batch Zipping**: Compress all successfully completed files into a single ZIP archive for one-click downloads.

### 3. OCR & AI Summarization
- **Scanned Text Extraction**: Translates scanned PDFs and images into structured text using Tesseract.
- **AI Document Summarizer**: Leverages Google Gemini API (with a local extractive text ranker fallback) to summarize long documents.

### 4. Real-Time WS Updates & Previews
- **WebSocket Broadcasts**: Shows real-time progress bars as tasks execute.
- **File Previews**: Live visual previews of images and text snippets before converting.

---

## 📡 API Reference Overview

### Health Checks
- `GET /api/v1/health/` — Validates DB, Redis Cache, and S3 Storage connection status (responds with 200 OK or 503 Service Unavailable).

### Authentication
- `POST /api/v1/auth/guest/` — Provision a temporary guest account.
- `POST /api/v1/auth/register/` / `login/` — Standard email registration and login (returns simple JWTs).

### Conversions & Sharing
- `POST /api/v1/conversions/batch/` — Start concurrent conversions.
- `POST /api/v1/conversions/<uuid:id>/share/` — Generate 24-hour cryptographic share links.
- `GET /api/v1/conversions/share/<str:token>/` — Public, unauthenticated file detail/download.

---

## 📊 Performance Metrics

We executed concurrent conversion load tests (Image -> JPG, Text -> PDF, ZIP Creation) using our benchmark suite:

| Load Size | Active Workers | Duration (s) | Success Rate | Throughput (files/s) | Avg Latency (ms) | P95 Latency (ms) |
|:---|:---|:---|:---|:---|:---|:---|
| **100 Files** | 8 | 0.13s | 100% | 742.83 | 8.39ms | 70.30ms |
| **500 Files** | 8 | 0.31s | 100% | 1624.36 | 2.94ms | 6.31ms |
| **1000 Files** | 8 | 0.61s | 100% | 1633.43 | 3.00ms | 6.44ms |

*To run benchmarks locally, execute: `python benchmark.py`*

---

## 🔒 Security Hardening & Observability

- **Sentry Error Tracking**: Full event capturing and profiling in production settings.
- **Structured Logging**: Log entries formatted as JSON structures using `python-json-logger`.
- **IP Rate Throttles**: Strict daily quota throttles (10 conversions/day for guests, 100 for registered users).
- **MIME Magic Verification**: Prevents extension spoofing by validating files using `python-magic`.

---

## 🚀 Quick Start (Local Docker Dev)

1. Clone repo & create env file:
   ```bash
   git clone <repo-url>
   cd cloud-file-converter
   cp .env.example .env
   ```
2. Launch Docker container stack:
   ```bash
   docker compose up -d
   ```
   *Access: Frontend at http://localhost:5173, API Docs at http://localhost:8000/api/docs/*

---

## 📂 Further Reading & Portfolio Resources

- **[Portfolio Case Study](file:///docs/portfolio_case_study.md)** — Architectural decisions, engineering challenges, and structural trade-offs.
- **[AWS Production Deployment Guide](file:///docs/deployment_guide.md)** — Complete Nginx reverse proxy configs, Supervisor daemon scripts, and CloudFront caching policies.
