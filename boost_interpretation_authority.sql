-- Increase authority level for all existing interpretations
-- This ensures they rank higher than regulations (level 10) in search results
UPDATE embeddings
SET authority_level = 12
WHERE source_type = 'interpretation';

-- Verify the update
SELECT source_type, count(*), avg(authority_level)
FROM embeddings
GROUP BY source_type;
