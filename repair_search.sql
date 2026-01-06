
-- ============================================================================
-- REPAIR SCRIPT: FIX VECTOR SEARCH ZERO RESULTS
-- ============================================================================
-- Problem: Search returns 0 results even though embeddings exist.
-- Cause: The 'embeddings_vector_idx' index handles 'approximate' search.
--        If created on an empty table, it may fail to find new records.
-- Fix:   Drop the index (force exact search) and update the function.
-- ============================================================================

-- 1. Drop the potential problem index
-- For dataset size < 2000, exact search (Sequential Scan) is faster and 100% accurate.
DROP INDEX IF EXISTS embeddings_vector_idx;

-- 2. Force refresh of the search function
CREATE OR REPLACE FUNCTION match_embeddings (
  query_embedding vector(768),
  match_count int DEFAULT 10
)
RETURNS TABLE (
  id uuid,
  source_id uuid,
  source_type text,
  content_chunk text,
  authority_level int,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    embeddings.id,
    embeddings.source_id,
    embeddings.source_type,
    embeddings.content_chunk,
    embeddings.authority_level,
    1 - (embeddings.embedding <=> query_embedding) AS similarity
  FROM embeddings
  ORDER BY embeddings.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 3. Verification (Optional)
-- Run this check to see if you have rows
SELECT count(*) as total_rows_in_embeddings_table FROM embeddings;
