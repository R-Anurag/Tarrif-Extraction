-- Tariff Extraction System Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main tariff events table
CREATE TABLE IF NOT EXISTS tariff_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
CREATE INDEX IF NOT EXISTS idx_content_hash ON tariff_events(content_hash);
CREATE INDEX IF NOT EXISTS idx_source ON tariff_events(source);
CREATE INDEX IF NOT EXISTS idx_validation_status ON tariff_events(validation_status);
CREATE INDEX IF NOT EXISTS idx_ingestion_timestamp ON tariff_events(ingestion_timestamp);
CREATE INDEX IF NOT EXISTS idx_hts_codes ON tariff_events USING GIN ((data->'tariff_action'->'products'));
CREATE INDEX IF NOT EXISTS idx_effective_date ON tariff_events((data->>'effective_date'));
CREATE INDEX IF NOT EXISTS idx_publication_date ON tariff_events((data->>'publication_date'));
CREATE INDEX IF NOT EXISTS idx_document_number ON tariff_events((data->>'fr_document_number'));
CREATE INDEX IF NOT EXISTS idx_full_text ON tariff_events USING GIN (to_tsvector('english', data::text));

-- Cross-reference tracking (lightweight relationship building)
CREATE TABLE IF NOT EXISTS document_relationships (
    id SERIAL PRIMARY KEY,
    parent_event_id UUID REFERENCES tariff_events(id) ON DELETE CASCADE,
    related_event_id UUID REFERENCES tariff_events(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50),
    confidence DECIMAL(3,2),
    matching_factors TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(parent_event_id, related_event_id)
);

CREATE INDEX IF NOT EXISTS idx_parent_event ON document_relationships(parent_event_id);
CREATE INDEX IF NOT EXISTS idx_related_event ON document_relationships(related_event_id);
