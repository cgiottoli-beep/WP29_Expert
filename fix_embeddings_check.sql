-- FIX EMBEDDINGS CHECK CONSTRAINT
-- The database is rejecting 'interpretation' because of a strict check on source_type.

-- 1. Drop the old constraint
ALTER TABLE embeddings 
DROP CONSTRAINT IF EXISTS embeddings_source_type_check;

-- 2. Add new constraint allowing 'interpretation'
-- We include 'document' (existing) and 'interpretation' (new).
ALTER TABLE embeddings 
ADD CONSTRAINT embeddings_source_type_check 
CHECK (source_type IN ('document', 'interpretation'));
