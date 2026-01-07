-- Function to get embedding counts for multiple documents in one query
-- This is much faster than individual queries from the client

CREATE OR REPLACE FUNCTION get_embedding_counts(doc_ids uuid[])
RETURNS TABLE(source_id uuid, count bigint)
LANGUAGE sql
SECURITY DEFINER  -- Runs with elevated privileges, bypasses RLS
AS $$
  SELECT e.source_id, COUNT(*) as count
  FROM embeddings e
  WHERE e.source_id = ANY(doc_ids)
  GROUP BY e.source_id;
$$;

-- Grant execute to authenticated and anonymous users
GRANT EXECUTE ON FUNCTION get_embedding_counts(uuid[]) TO authenticated;
GRANT EXECUTE ON FUNCTION get_embedding_counts(uuid[]) TO anon;
