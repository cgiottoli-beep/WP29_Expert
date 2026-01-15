SELECT 
    d.symbol,
    d.id as doc_id,
    COUNT(e.id) as embeddings,
    COUNT(*) FILTER (WHERE e.content_path IS NOT NULL) as in_storage,
    MIN(e.created_at) as first_created,
    MAX(e.created_at) as last_created
FROM documents d
JOIN embeddings e ON d.id = e.source_id
WHERE d.symbol = 'TFGP-04-03'
  AND e.created_at > NOW() - INTERVAL '10 minutes'
GROUP BY d.symbol, d.id;
