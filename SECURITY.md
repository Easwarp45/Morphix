# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x | ✅ Active |
| < 1.0 | ❌ No longer supported |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

If you discover a security vulnerability in Cloud File Converter, please report it responsibly:

1. **Email**: Send details to `security@cloudfileconverter.com` (replace with your actual email)
2. **Subject**: Use `[SECURITY] Brief description`
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Critical vulnerabilities patched within 14 days; others within 30 days
- **Credit**: You will be credited in the release notes (unless you prefer anonymity)

## Security Measures

This project implements the following security practices:

### Authentication
- JWT tokens with short expiry (15 minutes access, 7 days refresh)
- bcrypt password hashing
- Rate limiting on auth endpoints (5 requests/minute)
- Account lockout after repeated failures

### Transport Security
- HTTPS-only with HSTS (1 year, preload)
- TLS 1.2+ enforced
- Secure cookies only

### Data Protection
- S3 private buckets (no public access)
- Server-side encryption (AES-256) for all stored files
- Signed URLs for file access (time-limited)
- Automatic file deletion after 7 days

### Application Security
- CSRF protection on all state-changing endpoints
- XSS prevention headers
- SQL injection prevention via Django ORM parameterization
- Input validation on all file uploads
- Content-Type sniffing disabled

### Infrastructure
- Secrets managed via environment variables (never in code)
- Dependency auditing via `pip-audit`
- Sentry error monitoring (no PII in error reports)

## Known Security Considerations

- Files uploaded by users are not scanned for malware. Users should exercise caution when downloading converted files.
- OCR processing reads file content on the server. Ensure you only upload files you own or have permission to process.
