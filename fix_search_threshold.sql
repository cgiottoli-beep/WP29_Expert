-- FIX SEARCH THRESHOLD & RETURN TYPE
-- Error Fix: "Returned type uuid does not match expected type bigint in column 1"
-- This means the 'id' column in 'embeddings' table is a UUID, not a BIGINT.

-- 1. Drop the existing function to allow changing return type signature
DROP FUNCTION IF EXISTS match_embeddings(vector, int, float);

-- 2. Re-create with correct return types (id is UUID)
CREATE OR REPLACE FUNCTION match_embeddings (
  query_embedding vector(768),
  match_count int,
  filter_min_similarity float DEFAULT 0.1
) RETURNS TABLE (
  id uuid,             -- FIXED: changed from bigint to uuid
  source_id uuid,
  source_type text,
  content_chunk text,
  similarity float,
  authority_level int
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
    1 - (embeddings.embedding <=> query_embedding) AS similarity,
    embeddings.authority_level
  FROM embeddings
  WHERE 1 - (embeddings.embedding <=> query_embedding) > filter_min_similarity
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;

-- 3. Grant permissions
GRANT EXECUTE ON FUNCTION match_embeddings(vector, int, float) TO anon, authenticated, service_role;
