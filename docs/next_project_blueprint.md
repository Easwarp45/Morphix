# Next Project Blueprint — AI Resume Analyzer

A production-grade AI-powered resume analysis and career coaching platform. Designed as the natural sequel to Cloud File Converter, this project demonstrates **NLP, LLM integration, and user-facing AI features** — the most in-demand skills in 2024-2025.

---

## Product Vision

**"Get your resume past ATS filters and into the hands of hiring managers."**

Upload a resume + job description. Receive:
1. ATS compatibility score
2. Keyword gap analysis
3. Section-by-section feedback
4. Tailored rewrite suggestions (AI-powered)
5. Industry benchmarking

---

## Why This Project Next?

| Signal | Detail |
|--------|--------|
| **Market** | 250M+ resumes submitted annually in the US alone |
| **Tech** | Demonstrates LLM integration (GPT-4/Gemini), vector search, NLP |
| **Differentiation** | Shows AI product thinking, not just API calling |
| **Monetization** | Natural freemium model (3 analyses free, then subscription) |
| **Recruiter appeal** | "Built an AI tool that helps people get jobs" is a compelling story |

---

## Core Features (MVP)

### Free Tier
- [ ] Resume upload (PDF, DOCX)
- [ ] Job description paste or URL fetch
- [ ] ATS keyword match score (%)
- [ ] Top 10 missing keywords identified
- [ ] Basic section analysis (contact, summary, experience, education, skills)
- [ ] One free AI rewrite suggestion

### Authenticated Users
- [ ] Save analysis history (last 10)
- [ ] Compare resume against multiple job descriptions
- [ ] Download improved resume as PDF
- [ ] Email the analysis report

### AI-Powered (Gemini / GPT-4)
- [ ] Full resume critique with specific examples
- [ ] Tailored rewrite for each experience bullet
- [ ] Skills gap analysis with learning resource suggestions
- [ ] Interview question predictor based on resume + JD

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (Next.js 14)               │
│           React Server Components + Streaming UI         │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│               FastAPI Backend (Python 3.12)              │
│  /upload → /analyze → /improve → /export               │
└──────┬──────────────┬──────────────┬────────────────────┘
       │              │              │
  ┌────▼────┐   ┌─────▼─────┐  ┌────▼────────┐
  │ AWS S3  │   │  Celery   │  │  PostgreSQL │
  │ Uploads │   │  Workers  │  │  + pgvector │
  └─────────┘   └─────┬─────┘  └─────────────┘
                      │
              ┌───────▼────────┐
              │  AI Pipeline   │
              │  LlamaIndex    │
              │  Gemini API    │
              │  LangChain     │
              └────────────────┘
```

### New Skills Demonstrated (vs Cloud File Converter)
- **LLM Orchestration**: LangChain or LlamaIndex for chaining AI calls
- **Vector Search**: pgvector for semantic resume-JD matching
- **Streaming AI responses**: Real-time token-by-token output
- **Next.js 14**: React Server Components for SEO-optimized AI features
- **PDF generation**: Puppeteer or WeasyPrint for resume export

---

## Tech Stack Decision

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | Next.js 14 + TypeScript | SSR for SEO, RSC for streaming |
| Backend | FastAPI (Python) | Async-native, Pydantic validation, fastest REST framework |
| AI | Gemini 1.5 Pro | Long context (1M tokens), free tier, multimodal |
| NLP | spaCy + NLTK | Keyword extraction, entity recognition |
| Vector DB | pgvector (PostgreSQL) | No new infrastructure, semantic similarity |
| Storage | AWS S3 | Already familiar from Cloud File Converter |
| Queue | Celery + Redis | Same as Cloud File Converter |
| Deploy | Vercel (FE) + Render (BE) | Same as Cloud File Converter |

---

## Implementation Plan (12 Weeks)

| Week | Focus |
|------|-------|
| 1-2 | Project setup, auth, file upload (reuse Cloud File Converter patterns) |
| 3-4 | Resume parser (PDF/DOCX → structured JSON via spaCy) |
| 5-6 | ATS keyword matching engine (TF-IDF + semantic similarity via pgvector) |
| 7-8 | Gemini AI integration (resume critique, rewrite suggestions) |
| 9 | Streaming UI (real-time AI responses with Next.js streaming) |
| 10 | PDF export (improved resume download) |
| 11 | Analytics dashboard (user's improvement over time) |
| 12 | Polish, tests, deployment, documentation |

---

## Key Technical Challenges (Interview Stories)

1. **Parsing diverse resume formats**: PDFs created from Word, scanned PDFs, multi-column layouts — each requires different parsing strategies
2. **ATS simulation accuracy**: Real ATS systems are proprietary; must make statistical approximations
3. **LLM output consistency**: AI rewrites need deterministic structure — prompt engineering + output parsers
4. **Streaming large responses**: Gemini can take 30+ seconds for full analysis — streaming keeps UX responsive

---

## Alternative: Job Market Analytics Dashboard

If you prefer a data engineering / analytics focus:

| Feature | Tech |
|---------|------|
| Job posting scraper | Scrapy + Playwright |
| Data pipeline | Apache Airflow |
| Analytics store | ClickHouse or BigQuery |
| Visualization | React + D3.js / Recharts |
| ML | Salary prediction model (scikit-learn) |
| API | FastAPI with GraphQL |

**Story**: "Built a platform that scraped 50K+ job postings and built salary prediction models — found that adding 'AWS' to your title increases listed salary by 18%."

---

## Recommendation

**Build AI Resume Analyzer.** It:
1. Directly solves a problem your interviewers understand personally
2. Demonstrates LLM integration (the hottest skill in 2024)
3. Has a clear user journey (upload → analyze → improve)
4. Can leverage patterns you already built in Cloud File Converter
5. Makes a compelling demo in interviews

Start with the `/goal` command to plan this as your next project.
