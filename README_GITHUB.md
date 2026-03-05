# Tariff Extraction System

Production-ready multi-source tariff data extraction and processing system.

## Features

- **Multi-source data collection**: Federal Register API, USTR web scraping, CBP CSMS
- **Advanced parsing**: HTML/PDF with pdfplumber, HTS code extraction
- **Validation & normalization**: Date/rate validation, confidence scoring
- **Real-time relationship building**: Cross-source document linking
- **Optimized deduplication**: In-memory hash-based duplicate detection
- **PostgreSQL storage**: JSONB with GIN indexes for fast queries

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- pip

### Installation

```bash
# Clone repository
git clone <repo-url>
cd Tarrif-Extraction

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

## Database Schema

PostgreSQL tables:
- `tariff_events` - Main tariff data with JSONB
- `document_relationships` - Cross-source document links

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
- `settings.py` - Database, storage paths
- `sources.yaml` - Rate limits, schedules
- `validation_rules.yaml` - HTS, date, rate rules

## Development

### Running Tests

```bash
python scripts/verify_system.py
```

### Code Structure

- **Connectors**: Fetch data from sources
- **Parsers**: Extract structured data from HTML/PDF
- **Validators**: Validate HTS codes, dates, rates
- **Normalizers**: Standardize fields, build relationships
- **Storage**: PostgreSQL + local file storage

## License

[Your License]

## Contributing

[Your Contributing Guidelines]
