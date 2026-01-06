-- Migration: Add regulation_mentioned column to documents table
-- Run this in Supabase SQL Editor

-- Add new column for storing all mentioned regulations as text
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS regulation_mentioned TEXT;

-- Add comment to explain the column
COMMENT ON COLUMN documents.regulation_mentioned IS 'Text field storing all regulations mentioned in document (e.g., "R48, R10"). Independent of FK constraint, always stored even if regulation does not exist in library.';

-- Create index for searching by mentioned regulations
CREATE INDEX IF NOT EXISTS idx_documents_regulation_mentioned 
ON documents USING gin(to_tsvector('english', regulation_mentioned));
