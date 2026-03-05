import psycopg2
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager
from typing import Optional, Dict, List
import uuid
from datetime import datetime
from config.settings import DB_CONFIG


class Database:
    def __init__(self):
        self.config = DB_CONFIG
    
    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(**self.config)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def insert_tariff_event(self, event_data: Dict) -> str:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                event_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO tariff_events (
                        id, content_hash, ingestion_timestamp, parser_version,
                        confidence_score, validation_status, source, source_priority,
                        data, raw_html_path, raw_pdf_path, raw_json_path, conflicts
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    event_id,
                    event_data['content_hash'],
                    event_data.get('ingestion_timestamp', datetime.utcnow()),
                    event_data['parser_version'],
                    event_data.get('confidence_score'),
                    event_data.get('validation_status', 'pending'),
                    event_data['source'],
                    event_data['source_priority'],
                    Json(event_data['data']),
                    event_data.get('raw_html_path'),
                    event_data.get('raw_pdf_path'),
                    event_data.get('raw_json_path'),
                    Json(event_data.get('conflicts', []))
                ))
                return event_id
    
    def get_event_by_hash(self, content_hash: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM tariff_events WHERE content_hash = %s", (content_hash,))
                return cur.fetchone()
    
    def get_existing_hashes(self, source: str = None) -> set:
        """Get all existing content hashes for fast duplicate checking"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if source:
                    cur.execute("SELECT content_hash FROM tariff_events WHERE source = %s", (source,))
                else:
                    cur.execute("SELECT content_hash FROM tariff_events")
                return {row[0] for row in cur.fetchall()}
    
    def get_all_events(self, limit: int = None) -> List[Dict]:
        """Get all events for relationship building"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM tariff_events ORDER BY ingestion_timestamp DESC"
                if limit:
                    query += f" LIMIT {limit}"
                cur.execute(query)
                return cur.fetchall()
    
    def insert_relationship(self, parent_id: str, related_id: str, rel_type: str, confidence: float, factors: List[str]):
        """Insert document relationship"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO document_relationships 
                    (parent_event_id, related_event_id, relationship_type, confidence, matching_factors)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (parent_event_id, related_event_id) DO NOTHING
                """, (parent_id, related_id, rel_type, confidence, factors))
    
    def find_related_events(self, source: str, hts_codes: List[str], pub_date: str, limit: int = 10) -> List[Dict]:
        """Find existing events from other sources with matching HTS codes or dates"""
        if not hts_codes:
            return []
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, source, data
                    FROM tariff_events
                    WHERE source != %s
                    AND (
                        data->'tariff_action'->'products' @> ANY(ARRAY(SELECT jsonb_build_array(jsonb_build_object('hts_code', code)) FROM unnest(%s::text[]) AS code))
                        OR ABS(EXTRACT(EPOCH FROM (data->>'publication_date')::date - %s::date)) < 2592000
                    )
                    ORDER BY ingestion_timestamp DESC
                    LIMIT %s
                """, (source, hts_codes, pub_date, limit))
                return cur.fetchall()
