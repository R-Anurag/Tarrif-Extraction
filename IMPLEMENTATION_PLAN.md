# Comprehensive Tariff Extraction System - Implementation Plan

## 1. System Architecture (Enhanced)

```
┌─────────────────────────────────────────────────────────────┐
│                    Scheduler / Orchestrator                  │
│              (Airflow/Prefect + Circuit Breakers)           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Source Connectors Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │Federal Reg   │  │    USTR      │  │  CBP CSMS    │     │
│  │API (Primary) │  │ RSS→Scraper  │  │  RSS Feed    │     │
│  │Rate: 1000/hr │  │Rate: 60/min  │  │Rate: 120/min │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Raw Document Storage                        │
│         S3/Local: raw_html, raw_pdf, raw_json               │
│              + Content Hash + Metadata                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Document Parsing + Extraction                   │
│  PDF: pdfplumber → camelot → OCR → Manual Queue            │
│  HTML: lxml → BeautifulSoup                                 │
│  HTS Detection: Regex + Validation                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Validation Layer                          │
│  • HTS Format Check  • Date Logic  • Rate Format           │
│  • Required Fields   • Confidence Scoring                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Normalization Layer                        │
│  Cross-Source Correlation + Conflict Resolution             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Deduplication Engine                        │
│            SHA-256 Hash of Normalized Fields                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Tariff Event JSON                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL JSONB Database                       │
│                  + ElasticSearch                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Event Publisher                           │
│         Webhooks/Message Queue for Subscribers              │
└─────────────────────────────────────────────────────────────┘
```

## 2. Enhanced Database Schema

### PostgreSQL Tables

```sql
-- Main tariff events table
CREATE TABLE tariff_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    
    -- Metadata
    ingestion_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    parser_version VARCHAR(20) NOT NULL,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    validation_status VARCHAR(20) CHECK (validation_status IN ('verified', 'pending', 'failed', 'manual_review')),
    last_verified_date TIMESTAMPTZ,
    
    -- Source priority
    source VARCHAR(50) NOT NULL,
    source_priority INTEGER NOT NULL,
    
    -- Core data (JSONB for flexibility)
    data JSONB NOT NULL,
    
    -- Raw storage references
    raw_html_path TEXT,
    raw_pdf_path TEXT,
    raw_json_path TEXT,
    
    -- Conflict tracking
    conflicts JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_content_hash ON tariff_events(content_hash);
CREATE INDEX idx_source ON tariff_events(source);
CREATE INDEX idx_validation_status ON tariff_events(validation_status);
CREATE INDEX idx_ingestion_timestamp ON tariff_events(ingestion_timestamp);
CREATE INDEX idx_hts_codes ON tariff_events USING GIN ((data->'tariff_action'->'products'));
CREATE INDEX idx_effective_date ON tariff_events((data->>'effective_date'));
CREATE INDEX idx_publication_date ON tariff_events((data->>'publication_date'));
CREATE INDEX idx_document_number ON tariff_events((data->>'fr_document_number'));
CREATE INDEX idx_full_text ON tariff_events USING GIN (to_tsvector('english', data::text));

-- Cross-reference tracking
CREATE TABLE document_relationships (
    id SERIAL PRIMARY KEY,
    parent_event_id UUID REFERENCES tariff_events(id),
    related_event_id UUID REFERENCES tariff_events(id),
    relationship_type VARCHAR(50), -- 'implements', 'amends', 'references', 'supersedes'
    confidence DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_parent_event ON document_relationships(parent_event_id);
CREATE INDEX idx_related_event ON document_relationships(related_event_id);

-- Processing queue for failed/manual review items
CREATE TABLE processing_queue (
    id SERIAL PRIMARY KEY,
    event_id UUID REFERENCES tariff_events(id),
    queue_type VARCHAR(50), -- 'parsing_failed', 'validation_failed', 'manual_review', 'ocr_needed'
    priority INTEGER DEFAULT 5,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX idx_queue_type ON processing_queue(queue_type, processed_at);

-- Monitoring and observability
CREATE TABLE ingestion_metrics (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value DECIMAL,
    metadata JSONB,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_metrics_source ON ingestion_metrics(source, recorded_at);
CREATE INDEX idx_metrics_type ON ingestion_metrics(metric_type, recorded_at);
```

### Enhanced JSON Schema

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "content_hash": "sha256:abc123...",
  "ingestion_timestamp": "2024-01-15T10:30:00Z",
  "parser_version": "1.2.0",
  "confidence_score": 0.95,
  "validation_status": "verified",
  "last_verified_date": "2024-01-15T10:30:00Z",
  
  "source": "federal_register",
  "source_priority": 1,
  "document_type": "Presidential Proclamation",
  "title": "Adjusting Imports of Steel into the United States",
  
  "publication_date": "2024-05-12",
  "effective_date": "2024-05-15",
  "expiration_date": null,
  
  "identifiers": {
    "fr_document_number": "2024-10231",
    "proclamation_number": "10231",
    "executive_order_number": null,
    "cbp_csms_number": null
  },
  
  "tariff_action": {
    "type": "increase",
    "rate_original": "25%",
    "rate_normalized": 0.25,
    "rate_type": "ad_valorem",
    "legal_authority": "Section 232",
    "products": [
      {
        "hts_code": "7206.10.0000",
        "hts_code_validated": true,
        "description": "Iron and nonalloy steel ingots",
        "country_specific": ["CN", "RU"],
        "exclusions": []
      }
    ]
  },
  
  "related_documents": [
    {
      "type": "ustr_annex",
      "reference": "USTR Annex 1",
      "url": "https://ustr.gov/...",
      "document_id": "uuid-ref"
    },
    {
      "type": "cbp_implementation",
      "reference": "CBP CSMS #6102452",
      "url": "https://cbp.gov/...",
      "document_id": "uuid-ref"
    }
  ],
  
  "source_url": "https://federalregister.gov/...",
  "pdf_url": "https://federalregister.gov/.../pdf",
  
  "conflicts": [
    {
      "field": "effective_date",
      "values": {
        "federal_register": "2024-05-15",
        "cbp_csms": "2024-05-20"
      },
      "resolved_value": "2024-05-20",
      "resolution_rule": "cbp_implementation_precedence",
      "resolved_at": "2024-01-15T10:35:00Z"
    }
  ],
  
  "extraction_metadata": {
    "hts_extraction_method": "regex",
    "table_extraction_method": "pdfplumber",
    "ocr_used": false,
    "manual_review_required": false
  }
}
```

## 3. Project Structure

```
tariff-extraction/
├── config/
│   ├── settings.py              # Environment configs
│   ├── sources.yaml             # Source definitions & rate limits
│   ├── parsers.yaml             # Parser configurations
│   ├── validation_rules.yaml    # Validation rules
│   └── conflict_resolution.yaml # Conflict resolution rules
├── src/
│   ├── connectors/
│   │   ├── base.py              # Base connector class
│   │   ├── federal_register.py
│   │   ├── ustr.py
│   │   └── cbp.py
│   ├── parsers/
│   │   ├── base.py
│   │   ├── pdf_parser.py        # pdfplumber → camelot → OCR
│   │   ├── html_parser.py
│   │   └── hts_extractor.py
│   ├── validators/
│   │   ├── hts_validator.py
│   │   ├── date_validator.py
│   │   └── rate_validator.py
│   ├── normalizers/
│   │   ├── field_normalizer.py
│   │   └── cross_reference.py
│   ├── deduplication/
│   │   └── hasher.py
│   ├── storage/
│   │   ├── database.py
│   │   ├── s3_storage.py
│   │   └── elasticsearch.py
│   ├── monitoring/
│   │   ├── metrics.py
│   │   ├── circuit_breaker.py
│   │   └── alerting.py
│   ├── events/
│   │   └── publisher.py
│   └── utils/
│       ├── rate_limiter.py
│       └── retry.py
├── workflows/
│   ├── federal_register_dag.py
│   ├── ustr_dag.py
│   └── cbp_dag.py
├── tests/
├── scripts/
│   ├── init_db.sql
│   └── backfill.py
├── requirements.txt
└── docker-compose.yml
```

## 4. Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Deliverables:**
- Database schema setup
- Base connector class with rate limiting
- Raw storage (S3/local filesystem)
- Basic monitoring framework

**Files to create:**
1. `config/settings.py`
2. `src/storage/database.py`
3. `src/connectors/base.py`
4. `src/utils/rate_limiter.py`
5. `src/monitoring/metrics.py`
6. `scripts/init_db.sql`

### Phase 2: Federal Register Connector (Week 2-3)

**Deliverables:**
- Federal Register API connector
- HTML parser
- PDF parser (pdfplumber)
- HTS code extraction
- Basic validation

**Files to create:**
1. `src/connectors/federal_register.py`
2. `src/parsers/html_parser.py`
3. `src/parsers/pdf_parser.py`
4. `src/parsers/hts_extractor.py`
5. `src/validators/hts_validator.py`
6. `workflows/federal_register_dag.py`

### Phase 3: Validation & Normalization (Week 3-4)

**Deliverables:**
- Complete validation layer
- Field normalization
- Deduplication engine
- Confidence scoring

**Files to create:**
1. `src/validators/date_validator.py`
2. `src/validators/rate_validator.py`
3. `src/normalizers/field_normalizer.py`
4. `src/deduplication/hasher.py`

### Phase 4: Additional Sources (Week 4-5)

**Deliverables:**
- USTR connector (RSS + scraper)
- CBP connector (RSS)
- Cross-reference engine
- Conflict resolution

**Files to create:**
1. `src/connectors/ustr.py`
2. `src/connectors/cbp.py`
3. `src/normalizers/cross_reference.py`
4. `workflows/ustr_dag.py`
5. `workflows/cbp_dag.py`

### Phase 5: Advanced Features (Week 5-6)

**Deliverables:**
- OCR fallback for scanned PDFs
- Circuit breakers
- Event publishing system
- ElasticSearch integration
- Manual review queue

**Files to create:**
1. `src/parsers/ocr_parser.py`
2. `src/monitoring/circuit_breaker.py`
3. `src/events/publisher.py`
4. `src/storage/elasticsearch.py`

### Phase 6: Testing & Hardening (Week 6-7)

**Deliverables:**
- Comprehensive test suite
- Error handling improvements
- Documentation
- Backfill scripts

## 5. Core Configuration Files

### 5.1 Source Priority & Rate Limiting

**config/sources.yaml**
```yaml
sources:
  federal_register:
    priority: 1
    base_url: "https://www.federalregister.gov/api/v1"
    rate_limit: 1000  # per hour
    retry_attempts: 3
    timeout: 30
    schedule: "15 6,12,18 * * *"  # 6:15 AM, 12:15 PM, 6:15 PM ET
    
  cbp_csms:
    priority: 2
    base_url: "https://content.govdelivery.com/accounts/USDHSCBP/bulletins.rss"
    rate_limit: 120  # per minute
    retry_attempts: 3
    timeout: 30
    schedule: "*/30 * * * *"  # Every 30 minutes
    
  ustr:
    priority: 3
    base_url: "https://ustr.gov"
    rate_limit: 60  # per minute
    retry_attempts: 3
    timeout: 30
    schedule: "0 8 * * *"  # Daily at 8 AM
```

### 5.2 Validation Rules

**config/validation_rules.yaml**
```yaml
hts_code:
  pattern: "^\\d{4}\\.\\d{2}\\.\\d{4}$"
  length: 13
  validate_against_usitc: true

date_logic:
  - rule: "effective_date >= publication_date"
    severity: "error"
  - rule: "expiration_date > effective_date"
    severity: "warning"

rate_format:
  types: ["ad_valorem", "specific", "compound"]
  ad_valorem_pattern: "^\\d+(\\.\\d+)?%$"
  specific_pattern: "^\\$\\d+(\\.\\d+)?\\s*(per|/)"

required_fields:
  - source
  - document_type
  - title
  - publication_date
  - tariff_action.type
  - source_url
```

### 5.3 Conflict Resolution Rules

**config/conflict_resolution.yaml**
```yaml
resolution_rules:
  effective_date:
    priority_order: ["cbp_csms", "federal_register", "ustr"]
    reason: "CBP implementation date is authoritative"
    
  tariff_rate:
    priority_order: ["cbp_csms", "federal_register", "ustr"]
    reason: "CBP operational instructions override policy"
    
  hts_codes:
    strategy: "union"
    reason: "Combine all HTS codes from sources, validate each"
    
  product_description:
    priority_order: ["federal_register", "ustr", "cbp_csms"]
    reason: "Federal Register has legal description"
```

### 5.4 Circuit Breaker Configuration

**config/circuit_breakers.yaml**
```yaml
circuit_breakers:
  parsing_failure:
    threshold: 0.5  # 50% failure rate
    window: 3600    # 1 hour
    action: "halt_and_alert"
    
  source_unavailable:
    threshold: 3    # 3 consecutive failures
    action: "skip_and_alert"
    cooldown: 1800  # 30 minutes
    
  validation_failure:
    threshold: 0.3  # 30% failure rate
    window: 3600
    action: "continue_and_alert"
```

## 6. Key Algorithms

### 6.1 Content Hashing for Deduplication

```python
def generate_content_hash(data: dict) -> str:
    """Generate SHA-256 hash from normalized fields"""
    normalized_fields = {
        'source': data.get('source'),
        'document_type': data.get('document_type'),
        'publication_date': data.get('publication_date'),
        'fr_document_number': data.get('identifiers', {}).get('fr_document_number'),
        'hts_codes': sorted([p['hts_code'] for p in data.get('tariff_action', {}).get('products', [])]),
        'rate': data.get('tariff_action', {}).get('rate_normalized')
    }
    content = json.dumps(normalized_fields, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()
```

### 6.2 Confidence Scoring

```python
def calculate_confidence_score(data: dict, extraction_metadata: dict) -> float:
    """Calculate confidence score 0.0-1.0"""
    score = 1.0
    
    # Deduct for missing optional fields
    if not data.get('effective_date'): score -= 0.1
    if not data.get('identifiers', {}).get('fr_document_number'): score -= 0.15
    
    # Deduct for extraction method quality
    if extraction_metadata.get('ocr_used'): score -= 0.2
    if extraction_metadata.get('table_extraction_method') == 'fallback': score -= 0.1
    
    # Deduct for unvalidated HTS codes
    products = data.get('tariff_action', {}).get('products', [])
    invalid_hts = sum(1 for p in products if not p.get('hts_code_validated'))
    if products:
        score -= (invalid_hts / len(products)) * 0.2
    
    # Bonus for cross-references
    if len(data.get('related_documents', [])) > 0: score += 0.05
    
    return max(0.0, min(1.0, score))
```

### 6.3 Cross-Reference Matching

```python
def find_related_documents(current_doc: dict, existing_docs: list) -> list:
    """Find related documents using multiple heuristics"""
    matches = []
    
    for doc in existing_docs:
        confidence = 0.0
        relationship_type = None
        
        # Match by document numbers
        if current_doc.get('identifiers', {}).get('fr_document_number') == \
           doc.get('identifiers', {}).get('fr_document_number'):
            confidence = 1.0
            relationship_type = 'duplicate'
        
        # Match by HTS codes overlap
        current_hts = set(p['hts_code'] for p in current_doc.get('tariff_action', {}).get('products', []))
        doc_hts = set(p['hts_code'] for p in doc.get('tariff_action', {}).get('products', []))
        overlap = len(current_hts & doc_hts)
        if overlap > 0:
            confidence = max(confidence, overlap / len(current_hts | doc_hts))
            relationship_type = 'references'
        
        # Match by date proximity and keywords
        date_diff = abs((parse_date(current_doc['publication_date']) - 
                        parse_date(doc['publication_date'])).days)
        if date_diff <= 7:
            title_similarity = calculate_similarity(current_doc['title'], doc['title'])
            if title_similarity > 0.7:
                confidence = max(confidence, title_similarity * 0.8)
                relationship_type = 'amends' if 'amend' in current_doc['title'].lower() else 'implements'
        
        if confidence > 0.5:
            matches.append({
                'document_id': doc['id'],
                'confidence': confidence,
                'relationship_type': relationship_type
            })
    
    return matches
```

## 7. Monitoring & Observability

### Metrics to Track

```python
METRICS = {
    # Ingestion metrics
    'documents_fetched': Counter,
    'documents_processed': Counter,
    'documents_failed': Counter,
    'processing_duration': Histogram,
    
    # Source metrics
    'source_availability': Gauge,
    'source_response_time': Histogram,
    'rate_limit_hits': Counter,
    
    # Parsing metrics
    'parsing_success_rate': Gauge,
    'hts_extraction_count': Counter,
    'ocr_fallback_count': Counter,
    'manual_review_queue_size': Gauge,
    
    # Validation metrics
    'validation_failures': Counter,
    'confidence_score_distribution': Histogram,
    'hts_validation_failures': Counter,
    
    # Cross-reference metrics
    'cross_reference_matches': Counter,
    'conflict_resolutions': Counter,
    
    # Deduplication metrics
    'duplicates_detected': Counter,
    
    # Time-to-ingestion
    'publication_to_db_latency': Histogram
}
```

### Alert Conditions

**config/alerts.yaml**
```yaml
alerts:
  - name: "High Parsing Failure Rate"
    condition: "parsing_failure_rate > 0.3"
    window: "1h"
    severity: "critical"
    
  - name: "Source Unavailable"
    condition: "source_availability == 0"
    duration: "15m"
    severity: "high"
    
  - name: "Manual Review Queue Backlog"
    condition: "manual_review_queue_size > 100"
    severity: "medium"
    
  - name: "Ingestion Lag"
    condition: "publication_to_db_latency > 3600"
    severity: "medium"
    
  - name: "Circuit Breaker Triggered"
    condition: "circuit_breaker_open == true"
    severity: "critical"
```

## 8. Deployment Strategy

### Docker Compose Setup

**docker-compose.yml**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: tariff_db
      POSTGRES_USER: tariff_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
  
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - es_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"
  
  airflow-webserver:
    build: .
    command: webserver
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://tariff_user:${DB_PASSWORD}@postgres/tariff_db
    depends_on:
      - postgres
      - redis
    ports:
      - "8080:8080"
  
  airflow-scheduler:
    build: .
    command: scheduler
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://tariff_user:${DB_PASSWORD}@postgres/tariff_db
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  es_data:
```

### Requirements

**requirements.txt**
```
# Core
python>=3.10

# Web & API
requests>=2.31.0
httpx>=0.25.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
playwright>=1.40.0

# PDF Processing
pdfplumber>=0.10.0
camelot-py>=0.11.0
tabula-py>=2.8.0
pytesseract>=0.3.10

# Data Processing
pandas>=2.1.0
numpy>=1.24.0

# Database
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0
elasticsearch>=8.11.0

# Workflow
apache-airflow>=2.7.0
redis>=5.0.0

# Monitoring
prometheus-client>=0.19.0

# NLP (optional)
spacy>=3.7.0

# Utilities
pyyaml>=6.0
python-dotenv>=1.0.0
```

## 9. Testing Strategy

### Test Coverage Requirements

```
Unit Tests (70% coverage minimum):
- Parsers (HTS extraction, PDF parsing, HTML parsing)
- Validators (HTS format, date logic, rate format)
- Normalizers (field normalization, conflict resolution)
- Deduplication (hash generation, duplicate detection)

Integration Tests:
- End-to-end pipeline (raw document → database)
- Cross-source correlation
- Database operations
- API connectors (with mocked responses)

Performance Tests:
- 1000 documents/hour throughput
- Parser performance on large PDFs
- Database query performance
- Rate limiter accuracy
```

### Test Structure

```
tests/
├── unit/
│   ├── test_parsers.py
│   ├── test_validators.py
│   ├── test_normalizers.py
│   └── test_deduplication.py
├── integration/
│   ├── test_pipeline.py
│   ├── test_connectors.py
│   └── test_database.py
├── performance/
│   └── test_throughput.py
└── fixtures/
    ├── sample_documents/
    └── mock_responses/
```

## 10. Rollout Plan

### Week 1-2: Foundation
- Set up infrastructure (DB, S3, monitoring)
- Implement base classes and utilities
- Deploy monitoring dashboard

### Week 3-4: Federal Register Pipeline
- Deploy Federal Register connector
- Test with 30-day historical data
- Validate parsing accuracy (target: >90%)

### Week 5: Add CBP & USTR
- Deploy additional connectors
- Test cross-reference matching
- Validate conflict resolution

### Week 6-7: Production Hardening
- Load testing
- Security audit
- Documentation
- Training for manual review queue

### Week 8: Go Live
- Start with read-only mode
- Monitor for 1 week
- Enable full pipeline

## 11. Success Metrics

### Operational Metrics
- Uptime: >99.5%
- Parsing accuracy: >95%
- Time-to-ingestion: <1 hour from publication
- False positive rate (duplicates): <1%

### Quality Metrics
- HTS validation success: >98%
- Cross-reference match rate: >80%
- Manual review queue: <5% of total documents
- Confidence score average: >0.85

### Performance Metrics
- Documents processed: >100/day
- API response time: <500ms (p95)
- Database query time: <100ms (p95)

## 12. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Source structure changes | Schema drift detection + alerts |
| Rate limiting | Exponential backoff + distributed rate limiter |
| PDF parsing failures | Multi-tier fallback (pdfplumber → camelot → OCR) |
| Data quality issues | Validation layer + confidence scoring + manual queue |
| Database performance | Proper indexing + ElasticSearch for full-text |
| Legal compliance | Audit trail + last_verified_date + raw data preservation |

## 13. Future Enhancements (Post-MVP)

### Phase 7: Machine Learning Layer
- Auto-classify document types
- Predict effective dates
- Improve HTS extraction with NER models

### Phase 8: Additional Sources
- USITC HTS database
- WTO notifications
- Congressional legislation
- Trade association alerts

### Phase 9: API Layer
- REST API for querying tariff data
- Webhook subscriptions
- Real-time notifications

### Phase 10: Analytics Dashboard
- Tariff trend analysis
- Country-specific impact
- Industry sector analysis

## 14. Quick Start Guide

### Initial Setup

```bash
# Clone repository
git clone <repo-url>
cd tariff-extraction

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configurations

# Initialize database
psql -U postgres -f scripts/init_db.sql

# Start services
docker-compose up -d

# Run first ingestion
python scripts/backfill.py --source federal_register --days 30
```

### Development Workflow

```bash
# Run tests
pytest tests/

# Run linter
flake8 src/

# Run type checker
mypy src/

# Start Airflow
airflow webserver
airflow scheduler
```

## 15. Documentation Requirements

### Must Document
1. API endpoint specifications
2. Database schema with examples
3. Parser configuration guide
4. Troubleshooting common issues
5. Manual review queue procedures
6. Deployment runbook
7. Monitoring dashboard guide

### Code Documentation
- Docstrings for all public functions
- Type hints throughout
- README in each module
- Architecture decision records (ADRs)

---

## Summary

This implementation plan provides a complete roadmap for building a production-ready tariff extraction system. The architecture prioritizes:

1. **Reliability**: Multi-tier fallbacks, circuit breakers, retry logic
2. **Traceability**: Raw data preservation, audit trails, version tracking
3. **Accuracy**: Validation layers, confidence scoring, manual review queue
4. **Scalability**: Proper indexing, ElasticSearch, event-driven architecture
5. **Maintainability**: Modular design, comprehensive testing, monitoring

**Start with Phase 1** and iterate through each phase, validating success metrics before proceeding.
