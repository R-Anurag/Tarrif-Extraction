# Tariff Extraction System

Multi-source tariff data extraction and processing system.

## Features

- **Multi-source data collection**: Federal Register API, USTR web scraping, CBP CSMS  
- **Advanced parsing**: HTML/PDF with pdfplumber, HTS code extraction  
- **Validation & normalization**: Date/rate validation, confidence scoring  
- **Real-time relationship building**: Cross-source document linking  
- **Optimized deduplication**: In-memory hash-based duplicate detection  
- **PostgreSQL storage**: JSONB with GIN indexes for fast queries  
- **Production features**: Rate limiting, retry logic, error handling

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- pip

### Installation

```bash
# Clone repository
git clone <repo-url>
cd tariff-extraction

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
psql -U postgres -f scripts/init_db.sql
```

### Verify Installation

```bash
python scripts/verify_system.py
```

### Run Pipelines

```bash
# Federal Register (primary source - fast)
python workflows/federal_register_pipeline.py --days 1

# USTR fast mode (daily)
python workflows/ustr_pipeline_fast.py --days 1

# USTR full mode (weekly, includes PDFs)
python workflows/ustr_pipeline.py --days 7

# CBP CSMS (weekly)
python workflows/cbp_pipeline.py --days 7
```

## Architecture

```
Federal Register API → Parse → Validate → Normalize → Database
USTR Web Scraping   → Parse → Validate → Normalize → Database
CBP Web Scraping    → Parse → Validate → Normalize → Database
                                                    ↓
                                        Real-time Relationship Building
```

## Performance

- **Federal Register**: ~1-2s per document (API)
- **USTR Fast Mode**: ~3-5s per document (HTML only)
- **USTR Full Mode**: ~10-30s per document (includes PDFs)
- **Deduplication**: O(1) in-memory hash lookup
- **Throughput**: 100+ documents/day easily

## Database Schema

PostgreSQL tables:
- `tariff_events` - Main tariff data with JSONB (61 documents stored)
- `document_relationships` - Cross-source document links (real-time)

## Project Structure

```
tariff-extraction/
├── config/              # YAML configurations
├── src/
│   ├── connectors/      # Federal Register, USTR, CBP
│   ├── parsers/         # HTML, PDF, HTS extraction
│   ├── validators/      # HTS, date, rate, confidence
│   ├── normalizers/     # Field normalization, cross-ref
│   ├── deduplication/   # Content hashing
│   ├── storage/         # Database, local files
│   └── utils/           # Rate limiter, retry
├── workflows/           # Pipeline scripts
├── scripts/             # Setup & verification
└── data/raw/            # Downloaded files (not in git)
```

## Configuration

Edit `config/` files to customize:
- `settings.py` - Database, storage paths, parser version
- `sources.yaml` - Rate limits (1000/hr Federal Register, 60/min USTR/CBP)
- `validation_rules.yaml` - HTS format, date logic, rate patterns
- `conflict_resolution.yaml` - Source priority rules (unused - no conflicts found)

## Data Storage

**Database**: Structured, queryable data (JSONB)  
**Local Files**: Raw HTML/PDF for audit trail (data/raw/)  
- Preserves original sources for re-parsing and compliance  
- Not tracked in git (see .gitignore)

## Development

### System Verification

```bash
python scripts/verify_system.py
```

### Project Analysis

```bash
# Check project status
python scripts/analyze_project.py

# Check code coherence
python scripts/coherence_check.py
```

### Code Structure

- **Connectors**: Fetch data from sources (API + web scraping)
- **Parsers**: Extract structured data from HTML/PDF
- **Validators**: Validate HTS codes, dates, rates
- **Normalizers**: Standardize fields, build relationships
- **Storage**: PostgreSQL + local file storage
- **Utils**: Rate limiting, retry logic


## License

MIT License

## Contributing

Pull requests welcome. For major changes, please open an issue first.
