-- Vector Search RPC Function for Supabase
-- Add this to your init_database.sql or run separately after creating tables

-- Function to search embeddings using cosine similarity
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
