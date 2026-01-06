-- CLEAN ORPHANED EMBEDDINGS
-- Some embeddings may have been left behind when interpretations were deleted
-- before the cascading delete logic was implemented properly.
-- These "ghost" embeddings appear in search but point to nothing (Unknown Source).

BEGIN;

-- 1. Interpretations Orphans
DELETE FROM embeddings
WHERE source_type = 'interpretation'
AND source_id NOT IN (SELECT id FROM interpretations);

-- 2. Documents Orphans (just in case)
DELETE FROM embeddings
WHERE source_type = 'document'
AND source_id NOT IN (SELECT id FROM documents);

COMMIT;

-- Verify count
SELECT count(*) as proper_embeddings_count FROM embeddings;
