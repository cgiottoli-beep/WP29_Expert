-- UNECE WP.29 Archive - Database Initialization
-- Run this script in your Supabase SQL Editor

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- A. STRUCTURE & HIERARCHY
-- ============================================================================

-- Groups table (WP29, GRs, Task Forces)
CREATE TABLE IF NOT EXISTS groups (
    id TEXT PRIMARY KEY,  -- e.g., 'WP29', 'GRE', 'IWG-SLR'
    full_name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('WP', 'GR', 'IWG', 'TF', 'Committee')),
    parent_group_id TEXT REFERENCES groups(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id TEXT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    code TEXT NOT NULL,  -- e.g., '90'
    year INTEGER NOT NULL,
    dates TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(group_id, code)
);

-- ============================================================================
-- B. LEGAL FRAMEWORK (The "Law")
-- ============================================================================

-- Regulations table (abstract regulation)
CREATE TABLE IF NOT EXISTS regulations (
    id TEXT PRIMARY KEY,  -- e.g., 'R48', 'R10'
    title TEXT NOT NULL,
    topic TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Regulation versions (consolidated PDF files)
CREATE TABLE IF NOT EXISTS regulation_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    regulation_id TEXT NOT NULL REFERENCES regulations(id) ON DELETE CASCADE,
    series TEXT,  -- e.g., '09 Series'
    revision TEXT,  -- e.g., 'Rev. 14'
    status TEXT NOT NULL CHECK (status IN ('In Force', 'Superseded')),
    entry_date DATE,
    file_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- C. WORKING DOCUMENTS (The "Proposals")
-- ============================================================================

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,  -- e.g., 'ECE/TRANS/WP.29/GRE/2024/2' or 'GRE-90-02'
    title TEXT NOT NULL,
    author TEXT,  -- e.g., 'Italy', 'OICA'
    doc_type TEXT NOT NULL CHECK (doc_type IN ('Report', 'Agenda', 'Formal', 'Informal')),
    regulation_ref_id TEXT REFERENCES regulations(id) ON DELETE SET NULL,
    file_url TEXT,
    submission_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- D. AI & SEARCH (RAG)
-- ============================================================================

-- Embeddings table (unified vector store)
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL,  -- Reference to document.id or regulation_version.id
    source_type TEXT NOT NULL CHECK (source_type IN ('document', 'regulation')),
    content_chunk TEXT NOT NULL,
    embedding vector(768),  -- Gemini embedding dimension
    authority_level INTEGER NOT NULL,  -- 10 for Regulations/Reports, 1 for Proposals
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for vector similarity search (cosine distance)
CREATE INDEX IF NOT EXISTS embeddings_vector_idx 
ON embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_sessions_group_id ON sessions(group_id);
CREATE INDEX IF NOT EXISTS idx_documents_session_id ON documents(session_id);
CREATE INDEX IF NOT EXISTS idx_documents_regulation_ref ON documents(regulation_ref_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_regulation_versions_reg_id ON regulation_versions(regulation_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON embeddings(source_id, source_type);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE groups IS 'Hierarchical structure of WP29, GRs, and working groups';
COMMENT ON TABLE sessions IS 'Sessions held by groups';
COMMENT ON TABLE regulations IS 'Abstract regulations (e.g., R48, R10)';
COMMENT ON TABLE regulation_versions IS 'Specific versions of regulations with consolidated PDFs';
COMMENT ON TABLE documents IS 'Working documents submitted to sessions';
COMMENT ON TABLE embeddings IS 'Vector embeddings for RAG search across documents and regulations';

COMMENT ON COLUMN embeddings.authority_level IS '10=Regulation/Report (high authority), 1=Proposal (low authority)';
