# Case Study: Cloud File Converter Hardening

A detailed breakdown of technical decisions, scaling, and architectural choices made to build a production-ready, portfolio-grade cloud conversion platform.

---

## 1. Executive Summary

**Cloud File Converter** is a high-performance utility SaaS designed for rapid, on-demand conversion of documents, images, archives, text extraction (OCR), and document summarization. The platform prioritizes seamless guest access and system-level protection against API resource abuse.

---

## 2. Technical Decisions & Trade-Offs

### A. Local vs. API-Driven Operations
- **Decision**: Implemented a hybrid engine structure:
  - Text-extraction, format mapping, and image processing are handled **locally on CPU/memory** using compiled C-libraries (`PyMuPDF`, `Pillow`).
  - Heavy document summarization uses **external LLM APIs** (`Google Gemini API`) with a fast local counter fallback when API keys are absent.
- **Trade-Off**: Local processing requires greater server resource provisioning (more RAM/CPU on EC2 instances) but guarantees zero costs and high reliability for core conversion features.

### B. SQLite vs. PostgreSQL
- **Decision**: SQLite is utilized for development/testing, and PostgreSQL for production.
- **Trade-Off**: SQLite enables local database-less dev server runs and fast testing cycles. PostgreSQL enables reliable locking mechanisms and scalability under production load.

### C. Django Channels (ASGI) vs. Long Polling
- **Decision**: Configured ASGI with Django Channels and Daphne for real-time WebSocket state streaming.
- **Trade-Off**: WebSockets require persistent TCP connections (which increase memory consumption on load balancers/servers), but they deliver instant UI responses (zero-latency progress bars) and eliminate resource-intensive polling intervals.

---

## 3. Challenges Faced & Solutions

### A. Scanned Document OCR & PyMuPDF Saves
- **Problem**: Traditional PDF text extraction failed for scanned images. Additionally, attempting linear PDF saves using modern `PyMuPDF` version options caused compatibility errors.
- **Solution**:
  - Implemented page-by-page rendering: each PDF page is converted to an image and run through `pytesseract` to retrieve text.
  - Set `linear=False` during PyMuPDF document saves to avoid deprecation errors.

### B. Guest Account Cleanup Policies
- **Problem**: Allowing guest uploads without registration risks disk starvation (unlimited file storage).
- **Solution**:
  - Automatically allocate a guest user with unique JWT tokens and map them to `is_guest=True`.
  - Added a compound database index on `(user_id, expires_at)`.
  - Scheduled a Celery Beat daemon task running every 30 minutes to drop expired files from S3/DB and prune guest accounts.

---

## 4. Scalability & Reliability Considerations

1. **Celery Queue Isolation**:
   - Conversions are routed to multiple queues: `default` for standard operations, `heavy` for OCR/AI, and `priority` for registered users.
   - Resource-intensive tasks (e.g. processing scanned PDFs) cannot block short document conversions.
2. **CDN Edge Caching**:
   - Static bundles and icons are cached at CloudFront edges using strict `Cache-Control` configurations.
3. **Structured Observability**:
   - Structured JSON logging allows centralized log aggregators (e.g. AWS CloudWatch, Datadog) to parse event fields instantly.
   - System health endpoints check db/redis/storage connections before returning status to AWS Route53 or Load Balancers.
