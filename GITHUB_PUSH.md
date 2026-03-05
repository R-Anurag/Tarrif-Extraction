# GitHub Push Instructions

## Pre-Push Checklist

### 1. Verify .env is NOT tracked
```bash
# Check if .env is in git
git ls-files | grep .env

# If found, remove it
git rm --cached .env
```

### 2. Clean Python cache
```bash
# Remove all __pycache__ from git if tracked
git rm -r --cached **/__pycache__
```

### 3. Verify data files are NOT tracked
```bash
# Check for data files
git ls-files | grep "data/raw"

# Should only see .gitkeep files, not .html or .pdf
```

### 4. Run verification
```bash
python scripts/verify_system.py
```

## Initialize Git (if not already done)

```bash
cd "C:\Users\raian\Documents\GitHub\Tarrif Extraction"
git init
git branch -M main
```

## Add Files

```bash
# Add all files (respects .gitignore)
git add .

# Verify what will be committed
git status
```

## Commit

```bash
git commit -m "Initial commit: Production-ready tariff extraction system

Features:
- Multi-source data collection (Federal Register, USTR, CBP)
- HTML/PDF parsing with HTS code extraction
- Real-time relationship building
- Optimized deduplication
- PostgreSQL with JSONB storage"
```

## Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `tariff-extraction`
3. Description: `Production-ready multi-source tariff data extraction system`
4. Keep it Private (contains database structure)
5. Don't initialize with README (we have one)
6. Click "Create repository"

## Push to GitHub

```bash
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/tariff-extraction.git

# Push
git push -u origin main
```

## What Gets Pushed

✅ **Included:**
- All source code (src/, workflows/, scripts/)
- Configuration files (config/)
- Documentation (README.md, IMPLEMENTATION_PLAN.md)
- Requirements (requirements.txt)
- Database schema (scripts/init_db.sql)
- Empty data directories with .gitkeep

❌ **Excluded (via .gitignore):**
- .env (contains database password)
- data/raw/ files (157 HTML, 136 PDF files)
- __pycache__/ (Python cache)
- venv/ (virtual environment)
- *.pyc (compiled Python)
- IDE files (.vscode/, .idea/)

## After Push

### Clone on another machine:
```bash
git clone https://github.com/YOUR_USERNAME/tariff-extraction.git
cd tariff-extraction
cp .env.example .env
# Edit .env with credentials
pip install -r requirements.txt
psql -U postgres -f scripts/init_db.sql
python scripts/verify_system.py
```

## Security Notes

⚠️ **NEVER commit:**
- .env file (contains passwords)
- Database dumps
- API keys or tokens
- Personal data

✅ **Safe to commit:**
- .env.example (template with placeholders)
- Code and configuration
- Documentation
- Empty data structure
