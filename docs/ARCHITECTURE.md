# Cloud File Converter — Architecture Guide

## System Overview

Cloud File Converter is a monorepo SaaS application with a decoupled frontend/backend architecture communicating via REST API.

## Architecture Diagram

```
                        ┌──────────────────────────────────┐
                        │         Client Browser           │
                        │  React + TypeScript + Vite       │
                        │  ShadCN UI + Tailwind CSS        │
                        └────────────┬─────────────────────┘
                                     │ HTTPS (JWT Bearer)
                                     ▼
                        ┌──────────────────────────────────┐
                        │      Django REST Framework       │
                        │  ┌─────────────────────────────┐ │
                        │  │  Authentication Layer       │ │
                        │  │  (SimpleJWT + AllAuth)       │ │
                        │  ├─────────────────────────────┤ │
                        │  │  API Endpoints              │ │
                        │  │  /auth, /files, /conversions│ │
                        │  │  /analytics, /admin-panel   │ │
                        │  ├─────────────────────────────┤ │
                        │  │  Service Layer              │ │
                        │  │  FileService, ConversionSvc │ │
                        │  ├─────────────────────────────┤ │
                        │  │  Core Middleware            │ │
                        │  │  AuditLog, RequestID, CORS  │ │
                        │  └─────────────────────────────┘ │
                        └──────┬──────────┬────────────────┘
                               │          │
                    ┌──────────▼──┐  ┌────▼────────────┐
                    │ PostgreSQL  │  │     Redis        │
                    │ (Data)      │  │ (Broker+Cache)   │
                    └─────────────┘  └────┬────────────┘
                                          │
                               ┌──────────▼──────────┐
                               │   Celery Workers     │
                               │  ┌────────────────┐  │
                               │  │ Conversion      │  │
                               │  │ Engine          │  │
                               │  │ (Strategy       │  │
                               │  │  Pattern)       │  │
                               │  └──────┬─────────┘  │
                               └─────────┼────────────┘
                                          │
                               ┌──────────▼──────────┐
                               │   S3 Storage        │
                               │  (MinIO / AWS S3)   │
                               └─────────────────────┘
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
