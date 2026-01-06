-- UPDATE match_embeddings FUNCTION
-- The previous version of this function likely missed the 'source_type' column,
-- causing valid interpretations to show as "Unknown" in the AI search.

CREATE OR REPLACE FUNCTION match_embeddings (
  query_embedding vector(768),
  match_count int,
  filter_min_similarity float DEFAULT 0.5
) RETURNS TABLE (
  id bigint,
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
