# Contributing to Cloud File Converter

Thank you for your interest in contributing! This document outlines the process for contributing code, documentation, and bug reports.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

---

## Code of Conduct

This project adheres to the [Contributor Covenant](https://www.contributor-covenant.org/). By participating, you agree to maintain a respectful and inclusive environment for all contributors.

---

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/cloud-file-converter.git
   cd cloud-file-converter
   ```
3. **Add upstream** remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/cloud-file-converter.git
   ```

---

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Quick Start

```bash
# Start all services
docker-compose up -d

# Backend: create virtualenv and install deps
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements/development.txt

# Apply migrations
python manage.py migrate

# Run backend
python manage.py runserver

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend unit tests
cd backend
pytest --cov=apps --cov-report=term-missing

# E2E tests (requires running server)
cd ..
pip install requests websocket-client
pytest tests/e2e/ -v

# Frontend tests
cd frontend
npm test
```

---

## Making Changes

1. **Sync your fork** before starting:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or for bugs:
   git checkout -b fix/bug-description
   ```

3. **Make your changes** following the [Coding Standards](#coding-standards)

4. **Write/update tests** for your changes

5. **Run the full test suite** to ensure nothing is broken

6. **Commit** with a descriptive message:
   ```bash
   git commit -m "feat: add batch file download as ZIP"
   # or:
   git commit -m "fix: correct CORS origin validation for subdomains"
   ```
   Follow [Conventional Commits](https://www.conventionalcommits.org/) format.

---

## Pull Request Process

1. **Push** your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a Pull Request** on GitHub against the `main` branch

3. Fill in the PR template completely

4. Ensure all CI checks pass (tests, linting, type checking)

5. Request a review from a maintainer

6. Address any review comments

7. Once approved, a maintainer will merge your PR

### PR Checklist

- [ ] Tests written and passing
- [ ] Documentation updated (if applicable)
- [ ] No `print()` statements left in production code
- [ ] Environment variables documented in `docs/environment_variables.md`
- [ ] `CHANGELOG.md` updated

---

## Coding Standards

### Python (Backend)

- Follow **PEP 8** with a max line length of **100 characters**
- Use **type hints** for all function signatures
- Use `ruff` for linting: `ruff check .`
- Use `black` for formatting: `black .`
- Docstrings for all public methods using Google style

```python
def convert_file(file_path: str, target_format: str) -> ConversionResult:
    """
    Convert a file to the specified format.

    Args:
        file_path: Absolute path to the source file.
        target_format: Target file extension (e.g., 'pdf', 'docx').

    Returns:
        ConversionResult with status and output path.

    Raises:
        ConversionError: If the format is unsupported or conversion fails.
    """
```

### TypeScript (Frontend)

- Follow the existing ESLint configuration
- Use `interface` for object shapes, `type` for unions/intersections
- All components must be properly typed — no `any`
- Use React Query for server state, Zustand for client state

### Git Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use for |
|--------|---------|
| `feat:` | New features |
| `fix:` | Bug fixes |
| `docs:` | Documentation only |
| `style:` | Formatting, no logic change |
| `refactor:` | Code change without feature/fix |
| `test:` | Adding/fixing tests |
| `chore:` | Build process, dependencies |
| `perf:` | Performance improvements |

---

## Reporting Bugs

Use the [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) template. Include:

- **Clear description** of the problem
- **Steps to reproduce** (numbered list)
- **Expected behavior** vs **actual behavior**
- **Environment**: OS, Python version, browser
- **Logs or screenshots** if available

---

## Feature Requests

Use the [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) template. Include:

- **The problem** you're trying to solve
- **Your proposed solution**
- **Alternatives considered**
- **Additional context** (mockups, references)

---

## Questions?

Open a [Discussion](https://github.com/YOUR_USERNAME/cloud-file-converter/discussions) — issues are for bugs and feature requests only.
