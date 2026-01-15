-- FIX: Update match_embeddings RPC to include content_path
-- 
-- PROBLEM: The current RPC doesn't return content_path, causing
-- _populate_chunk_content to fail because it only downloads if
-- content_path is present but content_chunk is missing.
-- 
-- SOLUTION: Add content_path to the SELECT statement

-- Step 1: Drop existing function (required because we're changing return type)
DROP FUNCTION IF EXISTS match_embeddings(vector, integer, double precision);

-- Step 2: Create new function with content_path included
CREATE OR REPLACE FUNCTION match_embeddings(
  query_embedding vector(768),
  match_count int DEFAULT 10,
  filter_min_similarity float DEFAULT 0.5
)
RETURNS TABLE (
  id uuid,
  source_id uuid,
  source_type text,
  content_chunk text,
  content_path text,  -- ADDED THIS
  authority_level int,
  similarity float
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    embeddings.id,
    embeddings.source_id,
    embeddings.source_type,
    embeddings.content_chunk,
    embeddings.content_path,  -- ADDED THIS
    embeddings.authority_level,
    1 - (embeddings.embedding <=> query_embedding) AS similarity
  FROM embeddings
  WHERE 1 - (embeddings.embedding <=> query_embedding) > filter_min_similarity
  ORDER BY embeddings.embedding <=> query_embedding
  LIMIT match_count;
$$;
