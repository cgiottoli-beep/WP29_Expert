-- Verification Queries for RAG Storage System
-- Run these in Supabase SQL Editor to verify new documents are using Storage

-- ============================================================================
-- 1. Check if new documents have content_path (Storage-based)
-- ============================================================================

SELECT 
    COUNT(*) FILTER (WHERE content_path IS NOT NULL) as chunks_in_storage,
    COUNT(*) FILTER (WHERE content_chunk IS NOT NULL) as chunks_in_db,
    COUNT(*) as total_chunks,
    pg_size_pretty(SUM(pg_column_size(content_chunk))) as db_text_size,
    MAX(created_at::date) as latest_chunk_date
FROM embeddings;

-- Expected Result:
-- chunks_in_storage: Should be > 0 (new system working)
-- chunks_in_db: Should be 0 (all chunks should have NULL content)
-- latest_chunk_date: Should be today (2026-01-13)


-- ============================================================================
-- 2. Show recent embeddings with storage info
-- ============================================================================

SELECT 
    id,
    source_id,
    source_type,
    content_path,
    CASE 
        WHEN content_chunk IS NULL THEN '✓ Storage'
        ELSE '✗ Still in DB'
    END as storage_status,
    authority_level,
    created_at::date as created_date
FROM embeddings
ORDER BY created_at DESC
LIMIT 20;

-- Expected Result:
-- All recent rows should have:
--   - content_path: Something like "doc-id/chunk_0.json"
--   - storage_status: "✓ Storage"


-- ============================================================================
-- 3. Verify Storage bucket has files
-- ============================================================================

-- This query won't work in SQL, you need to check manually:
-- Go to: Supabase Dashboard → Storage → chunks_cache
-- You should see folders with document IDs containing .json files


-- ============================================================================
-- 4. Count documents by storage type
-- ============================================================================

SELECT 
    source_type,
    COUNT(DISTINCT source_id) as document_count,
    COUNT(*) as chunk_count,
    COUNT(*) FILTER (WHERE content_path IS NOT NULL) as in_storage,
    COUNT(*) FILTER (WHERE content_chunk IS NOT NULL) as in_db
FROM embeddings
GROUP BY source_type
ORDER BY source_type;

-- Expected Result:
-- in_storage should be > 0 for recent documents
-- in_db should be 0 (after migration)


-- ============================================================================
-- 5. Check specific document (replace with your document ID)
-- ============================================================================

-- First, find a recent document ID:
SELECT DISTINCT 
    e.source_id,
    d.symbol,
    d.title,
    COUNT(*) as chunk_count,
    COUNT(*) FILTER (WHERE e.content_path IS NOT NULL) as chunks_in_storage
FROM embeddings e
JOIN documents d ON e.source_id = d.id
WHERE e.created_at::date = CURRENT_DATE
GROUP BY e.source_id, d.symbol, d.title
ORDER BY e.source_id
LIMIT 5;

-- Then check one specific document:
-- SELECT * FROM embeddings WHERE source_id = 'YOUR-DOC-ID-HERE';
