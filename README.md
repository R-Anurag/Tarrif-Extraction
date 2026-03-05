# Tariff Extraction System

## Production-Ready Multi-Source Tariff Data Extraction

### Quick Start

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. **Initialize Database**
```bash
psql -U postgres -f scripts/init_db.sql
```

4. **Verify System**
```bash
python scripts/verify_system.py
```

5. **Run Pipelines**
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

### System Architecture

```
Federal Register API → Parse → Validate → Normalize → Database
USTR Web Scraping   → Parse → Validate → Normalize → Database
CBP Web Scraping    → Parse → Validate → Normalize → Database
                                                    ↓
                                        Cross-Reference & Conflict Resolution
```

### Features

✅ **Multi-Source Data Collection**
- Federal Register API (primary, 100+ documents)
- USTR web scraping (policy details, 20+ documents)
- CBP web scraping (implementation guidance)

✅ **Advanced Processing**
- HTML/PDF parsing with pdfplumber
- HTS code extraction & validation
- Date/rate validation & normalization
- Optimized deduplication (in-memory hashing)
- Confidence scoring (0.0-1.0)

✅ **Multi-Source Intelligence**
- Cross-reference engine (links related documents)
- Conflict resolver (priority-based merging)
- Source priority: CBP > Federal Register > USTR

✅ **Production Features**
- PostgreSQL with JSONB storage
- Local file storage (HTML/PDF/JSON)
- Rate limiting & retry logic
- Real-time relationship building
- Comprehensive error handling

### Performance

- **Federal Register**: ~1-2s per document (API)
- **USTR Fast Mode**: ~3-5s per document (HTML only)
- **USTR Full Mode**: ~10-30s per document (includes PDFs)
- **Deduplication**: O(1) in-memory hash lookup

### Database Schema

PostgreSQL tables:
- `tariff_events` - Main tariff data with JSONB
- `document_relationships` - Cross-source document links

### Project Structure

```
tariff-extraction/
├── config/              # YAML configurations
├── src/
│   ├── connectors/      # Federal Register, USTR, CBP
│   ├── parsers/         # HTML, PDF, HTS extraction
│   ├── validators/      # HTS, date, rate, confidence
│   ├── normalizers/     # Field normalization, cross-ref, conflicts
│   ├── deduplication/   # Content hashing
│   ├── storage/         # Database, local files
│   ├── utils/           # Rate limiter, retry
│   └── monitoring/      # Metrics
├── workflows/           # Pipeline scripts
├── scripts/             # Setup & verification
└── data/raw/            # Downloaded files
```

### Documentation

- `IMPLEMENTATION_PLAN.md` - Detailed technical plan
- `README.md` - This file
- `requirements.txt` - Python dependencies

---

**Built with**: Python, PostgreSQL, BeautifulSoup, pdfplumber, feedparser
