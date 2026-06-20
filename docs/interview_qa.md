# Cloud File Converter — Interview Preparation Guide

A comprehensive Q&A covering every dimension an interviewer might probe. Organized by topic with STAR-format answers where applicable.

---

## 1. Architecture & System Design

### Q: Walk me through the overall architecture of Cloud File Converter.

**A:** The platform is a cloud-native SaaS with three main layers:

1. **Presentation Layer** — React 18 + TypeScript SPA served via Vercel. Communicates with the backend via REST API and WebSockets for real-time updates.
2. **Application Layer** — Django + Django REST Framework handling business logic. Django Channels manages WebSocket connections for live conversion progress. Gunicorn with Uvicorn workers handles the ASGI server.
3. **Worker Layer** — Celery workers (backed by Redis as broker) process file conversions asynchronously. Celery Beat handles scheduled tasks like file cleanup.
4. **Data Layer** — PostgreSQL for relational data (users, files, jobs), Redis for caching + task queue, AWS S3 for file object storage with CloudFront CDN for distribution.

```
Client → [CloudFront / Vercel] → [Nginx] → [Gunicorn/Uvicorn] → [Django]
                                                                       ↓
                                                              [Celery Worker]
                                                                       ↓
                                                  [PostgreSQL] [Redis] [S3]
```

---

### Q: Why did you choose Celery + Redis over other async approaches?

**A:** Several reasons:
- **Reliability**: Celery provides task persistence — if a worker crashes mid-conversion, the task can be retried automatically.
- **Scalability**: Workers can be scaled horizontally independently of the web server. Adding more workers requires just spinning up new containers.
- **Ecosystem**: Rich ecosystem with Flower for monitoring, Django-Celery-Beat for scheduling, and extensive retry/error handling.
- **Alternatives considered**: Django background tasks (not distributed), AWS SQS (would add complexity and cost for MVP), asyncio (not suitable for CPU-bound conversion work).

---

### Q: How does the real-time progress feature work?

**A:** It uses Django Channels with WebSockets:
1. Client opens a WebSocket connection to `wss://api.domain.com/ws/conversions/?token=JWT`
2. Django Channels authenticates the token and assigns the connection to a channel group keyed by user ID
3. When Celery worker processes a conversion, it sends progress events (0%, 25%, 50%, 75%, 100%) to the channel layer (Redis pub/sub)
4. Channel layer delivers events to all open WebSocket connections for that user
5. Client receives JSON events like `{"type": "conversion.progress", "job_id": "...", "progress": 50}`

This avoids polling, reduces server load, and gives users instant feedback.

---

### Q: How does your system handle concurrent conversions?

**A:** At multiple levels:
1. **Task Queue**: Celery distributes tasks across N workers. Each worker handles one conversion at a time. Worker count scales with load.
2. **Worker Concurrency**: Each Celery worker can use `--concurrency=4` for I/O-bound tasks (network calls, simple format changes) or `--concurrency=1` for CPU-bound tasks (video encoding, OCR).
3. **Database Connection Pooling**: Django's DB connection pool prevents exhausting PostgreSQL connections under load.
4. **Rate Limiting**: Redis-based rate limiting prevents any single user from flooding the queue.

In benchmarks, 1,000 concurrent conversion tasks were processed with horizontal scaling to 4 workers.

---

### Q: How would you scale this to 100,000 daily users?

**A:** The architecture already supports horizontal scaling. The roadmap would be:

1. **Web Tier**: Auto-scaling EC2 group or Render auto-scale behind a load balancer. Stateless — any instance can serve any request.
2. **Database**: Read replicas for analytics queries, connection pooling via PgBouncer.
3. **Workers**: Separate worker pools by task type (high-priority, video, OCR) with different scaling policies.
4. **CDN**: CloudFront already handles file delivery — this doesn't scale with user count.
5. **Queue**: Redis Cluster for high availability. Consider SQS for very high throughput.
6. **Caching**: Redis caching for conversion format metadata, user quota lookups, and frequently accessed file metadata.

At 100K users, the bottleneck would be the conversion workers — that's where I'd invest in auto-scaling first.

---

## 2. Backend Engineering

### Q: Explain your approach to file storage and security.

**A:** Files are stored in AWS S3 with:
- **Private bucket** — no public access whatsoever
- **Signed URLs** — all file access uses pre-signed S3 URLs with 1-hour expiry
- **Server-side encryption** — AES-256 at rest
- **CloudFront OAC** — only CloudFront can read from S3; users never access S3 directly
- **Lifecycle rules** — files auto-deleted after 7 days; aborted multipart uploads cleaned up after 1 day

For shareable links, we generate a UUID token stored in our database with an expiry timestamp. The download endpoint validates the token and generates a fresh signed URL on demand.

---

### Q: How does your authentication work?

**A:** JWT-based:
- `POST /auth/register/` → returns `access` (15 min) + `refresh` (7 days) tokens
- `POST /auth/login/` → same
- `POST /auth/token/refresh/` → uses refresh token to get new access token
- All protected endpoints require `Authorization: Bearer <access_token>`

For Google OAuth, we use `dj-rest-auth` with `allauth`. The frontend gets a Google `id_token`, sends it to our `/auth/google/`, we verify it against Google's public keys, create or retrieve the user, and return our own JWT pair.

Security hardening:
- Refresh tokens are rotated on use (old one invalidated)
- Rate limiting: 5 login attempts per minute per IP
- Passwords hashed with bcrypt (Django default PBKDF2)

---

### Q: How did you implement the OCR feature?

**A:** Using Tesseract via `pytesseract` Python wrapper:
1. For image files (PNG, JPG, TIFF): convert directly with `pytesseract.image_to_string()`
2. For scanned PDFs: convert each page to an image using `pdf2image`, then OCR each page
3. Results are concatenated and returned as plain text or saved as a `.txt` file

Challenges:
- Tesseract accuracy depends on image quality. We added DPI normalization (300 DPI recommended)
- Large scanned PDFs can take minutes. These run in Celery workers with 10-minute timeout
- Memory: Processing a 200-page PDF creates 200 PIL images. We process pages sequentially and garbage collect between pages

---

### Q: Walk me through your AI summarization implementation.

**A:** Using Google Gemini API:
1. Extract text content from the file (using our text extraction pipeline)
2. Truncate to model context limit (~30K tokens)
3. Send to Gemini with a structured prompt asking for a bullet-point summary
4. Return the summary alongside the converted file

**Fallback strategy**: If `GEMINI_API_KEY` is missing or the API call fails, we fall back to a local extractive summarization: select the first sentence of each paragraph, deduplicate, and return the top N sentences by TF-IDF score.

This means the feature degrades gracefully rather than failing hard — important for reliability.

**Cost control**: Summarization is triggered explicitly by the user (not automatic), and we cache summaries by file hash to avoid re-processing identical uploads.

---

## 3. Cloud & Infrastructure

### Q: Explain your AWS architecture decisions.

**A:**
- **S3**: Object storage for uploads and converted files. Chose S3 for durability (11 9s), built-in lifecycle policies, native CloudFront integration, and cost (~$0.023/GB/month).
- **CloudFront**: CDN for file downloads. Reduces latency globally, reduces S3 egress costs, and adds a caching layer. Used OAC (Origin Access Control) so only CloudFront can access the S3 bucket.
- **EC2** (optional): For the backend API server. Could also use Render or Railway for simpler deployments.
- **RDS PostgreSQL**: Production database with automated backups.

**What I would add at scale**: ElastiCache (Redis managed), SQS instead of Redis for the task queue (better durability), Lambda for simple synchronous conversions, and S3 Select for partial file reads.

---

### Q: How does your CI/CD pipeline work?

**A:** GitHub Actions:
1. **On PR**: Run unit tests (matrix: Python 3.11, 3.12), ESLint, TypeScript type-check, `ruff` linting, `pip-audit` security scan
2. **On merge to main**: All of the above + `python manage.py check --deploy` + production Vite build
3. **Deploy**: Manual trigger (or webhook) runs `scripts/deploy.sh` on EC2 — pulls code, installs deps, migrates, collectstatic, restarts Gunicorn/Celery via Supervisor

I chose manual deploy triggers (rather than auto-deploy on push) for a portfolio project to avoid unexpected production changes. In a team environment, I'd use staged deployments with automated rollbacks.

---

## 4. Security Engineering

### Q: What security vulnerabilities did you design against?

**A:**

| Threat | Mitigation |
|--------|-----------|
| SQL Injection | Django ORM parameterized queries, never raw SQL with user input |
| XSS | React auto-escapes, `X-Content-Type-Options: nosniff` header, CSP |
| CSRF | Django CSRF middleware, `SameSite=Strict` cookies |
| Auth brute force | Rate limiting (5 req/min), account lockout |
| Insecure file upload | MIME type validation, size limits, S3 private storage |
| Secrets exposure | Environment variables only, `.env` in `.gitignore`, CI secrets vault |
| MITM | HSTS (1 year, preload), HTTPS-only |
| Dependency vulnerabilities | `pip-audit` in CI, regular `npm audit` |

---

### Q: What would you do differently from a security perspective?

**A:**
1. **Malware scanning**: Integrate ClamAV to scan uploaded files before processing
2. **Content Security Policy**: Add a strict CSP header to prevent XSS via injected scripts
3. **WAF**: Add AWS WAF rules in front of CloudFront for SQL injection and known attack patterns
4. **Secrets rotation**: Use AWS Secrets Manager for rotating DB credentials
5. **Penetration testing**: Run OWASP ZAP or Burp Suite against the staging environment
6. **Audit logging**: Log all file access events to an immutable log store (AWS CloudTrail or similar)

---

## 5. Performance & Scalability

### Q: What were your benchmark results?

**A:** Using our `benchmark.py` script running concurrent Celery conversions:

| Test | Files | Workers | Total Time | Throughput | p95 Latency |
|------|-------|---------|-----------|-----------|------------|
| Smoke | 100 | 2 | ~45s | 2.2 files/s | 2.8s |
| Load | 500 | 4 | ~3.5m | 2.4 files/s | 3.1s |
| Stress | 1,000 | 4 | ~7.2m | 2.3 files/s | 3.4s |

The 1,000-file test showed consistent throughput with no worker crashes or queue backup, validating the architecture's stability under load.

---

### Q: What caching strategies did you implement?

**A:**
1. **Redis cache**: Conversion format metadata (supported formats list) cached for 24 hours — avoids DB queries on every upload
2. **User quota cache**: Current user's daily conversion count cached in Redis for fast rate limit checks
3. **CloudFront CDN**: Converted file downloads served from CDN edge nodes — global distribution reduces latency
4. **Django cache middleware**: Health check endpoint cached for 30 seconds to prevent DB hammering from uptime monitors
5. **S3 cache headers**: CloudFront-served files get `Cache-Control: max-age=86400` headers

---

## 6. Project & Leadership

### Q: What was the hardest technical challenge?

**A:** Implementing real-time conversion progress without polling.

**Situation**: Users uploading large files had no feedback during the 30-60 second conversion period.
**Task**: Implement live progress updates without degrading API performance.
**Action**: Evaluated SSE (Server-Sent Events), polling, and WebSockets. Chose WebSockets because they support bi-directional communication (useful for cancellation). Used Django Channels with Redis as the channel layer. Celery workers publish progress events to Redis, Channels delivers them to the WebSocket connection.
**Result**: Users see a progress bar updating every few seconds, improving perceived performance. Bounce rate on conversion page dropped significantly in user testing.

The hardest part was managing WebSocket authentication — HTTP cookies don't work for WebSocket upgrade requests, so I switched to passing the JWT in the query parameter for the initial handshake, then immediately validating and discarding it from memory.

---

### Q: If you had 3 more months, what would you build next?

**A:**
1. **Team Workspaces** — Shared conversion queues, admin permissions, usage analytics per team
2. **Mobile App** — React Native for iOS/Android with push notifications for conversion completion
3. **Plugin System** — Allow third-party converters to register via a plugin API (e.g., specialized scientific format converters)
4. **Webhook Integration** — Let users register webhooks to notify their own systems when conversions complete (Zapier-style)
5. **Conversion Templates** — Save compression settings, OCR language, output quality preferences as reusable templates

---

## 7. Behavioral Questions

### Q: How did you prioritize features for the MVP?

**A:** I applied the MoSCoW method:
- **Must Have**: Authentication, file upload, core conversions (PDF, DOCX, images), async processing
- **Should Have**: Real-time progress, history, shareable links, OCR
- **Could Have**: AI summarization, analytics dashboard, PWA
- **Won't Have (MVP)**: Mobile apps, team features, billing

The principle: get the core conversion pipeline working reliably first, then layer on UX improvements and advanced features.

### Q: How do you ensure code quality on a solo project?

**A:** Discipline and tooling:
- **Pre-commit hooks**: `ruff` + `black` run on every commit — no manual formatting
- **Test-first thinking**: Write tests before marking a feature done
- **Code review via PR**: Even solo, I create PRs from feature branches to main — forces me to review my own diff
- **CI gates**: Tests must pass before merge — CI acts as an objective code reviewer
- **Documentation as you go**: Write docstrings and update the README as features are built, not after

---

*Last updated: 2024-12-01 | Cloud File Converter v1.0.0*
