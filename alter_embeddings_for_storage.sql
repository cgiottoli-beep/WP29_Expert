-- Migration: Move chunk content from DB to Storage
-- Add content_path column and make content_chunk nullable

-- Add content_path column to store the Storage path for the chunk JSON
ALTER TABLE embeddings 
ADD COLUMN IF NOT EXISTS content_path TEXT;

-- Make content_chunk nullable (it will be phased out in favor of Storage)
ALTER TABLE embeddings 
ALTER COLUMN content_chunk DROP NOT NULL;

-- Add index on content_path for faster lookups
CREATE INDEX IF NOT EXISTS idx_embeddings_content_path 
ON embeddings(content_path) 
WHERE content_path IS NOT NULL;

-- Add comment to explain the new architecture
COMMENT ON COLUMN embeddings.content_path IS 'Path to JSON file in chunks_cache bucket containing chunk text and metadata';
COMMENT ON COLUMN embeddings.content_chunk IS 'DEPRECATED: Chunk text now stored in Storage. Legacy records may still have this populated.';
