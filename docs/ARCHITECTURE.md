# Morphix â€” Architecture Guide

## System Overview

Morphix is a monorepo SaaS application with a decoupled frontend/backend architecture communicating via REST API.

## Architecture Diagram

```
                        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                        â”‚         Client Browser           â”‚
                        â”‚  React + TypeScript + Vite       â”‚
                        â”‚  ShadCN UI + Tailwind CSS        â”‚
                        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                     â”‚ HTTPS (JWT Bearer)
                                     â–¼
                        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                        â”‚      Django REST Framework       â”‚
                        â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
                        â”‚  â”‚  Authentication Layer       â”‚ â”‚
                        â”‚  â”‚  (SimpleJWT + AllAuth)       â”‚ â”‚
                        â”‚  â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤ â”‚
                        â”‚  â”‚  API Endpoints              â”‚ â”‚
                        â”‚  â”‚  /auth, /files, /conversionsâ”‚ â”‚
                        â”‚  â”‚  /analytics, /admin-panel   â”‚ â”‚
                        â”‚  â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤ â”‚
                        â”‚  â”‚  Service Layer              â”‚ â”‚
                        â”‚  â”‚  FileService, ConversionSvc â”‚ â”‚
                        â”‚  â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤ â”‚
                        â”‚  â”‚  Core Middleware            â”‚ â”‚
                        â”‚  â”‚  AuditLog, RequestID, CORS  â”‚ â”‚
                        â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚
                        â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                               â”‚          â”‚
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”  â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚ PostgreSQL  â”‚  â”‚     Redis        â”‚
                    â”‚ (Data)      â”‚  â”‚ (Broker+Cache)   â”‚
                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                          â”‚
                               â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                               â”‚   Celery Workers     â”‚
                               â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
                               â”‚  â”‚ Conversion      â”‚  â”‚
                               â”‚  â”‚ Engine          â”‚  â”‚
                               â”‚  â”‚ (Strategy       â”‚  â”‚
                               â”‚  â”‚  Pattern)       â”‚  â”‚
                               â”‚  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
                               â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                          â”‚
                               â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                               â”‚   S3 Storage        â”‚
                               â”‚  (MinIO / AWS S3)   â”‚
                               â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## Design Patterns

### Backend
- **Service Layer Pattern**: Business logic is encapsulated in service classes (FileService, etc.), keeping views thin.
- **Strategy Pattern**: The conversion engine uses a registry of converter classes, each implementing a `BaseConverter` interface.
- **Repository Pattern**: Django ORM models with custom managers serve as the data access layer.
- **Middleware Pattern**: Audit logging and request ID assignment are handled via Django middleware.

### Frontend
- **Context Pattern**: Auth and Theme state managed via React Context + hooks.
- **Service Layer**: All API calls are abstracted into service modules (`auth.ts`, `index.ts`).
- **Component Composition**: Pages compose reusable layout and UI components.

## Database Schema

7 tables: Users, Files, Conversions, Downloads, Subscriptions, AuditLogs, Notifications.
All use UUID primary keys. See the ER diagram in the implementation plan.

## Security Architecture

- JWT tokens (15min access, 7d refresh with rotation and blacklisting)
- Rate limiting at multiple tiers (anon, auth, upload, conversion)
- File validation: extension whitelist + MIME type check
- S3 private buckets with pre-signed URLs
- Audit trail for all state-changing API requests
