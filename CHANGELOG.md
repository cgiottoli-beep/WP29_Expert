# Changelog

## [1.2.0] - 2026-01-15

### Added
- Implement automated semantic versioning and release management with a version bump script and GitHub Actions workflow.
- Add Smart Ingestion and Search Session pages, alongside new tests and utility scripts for document processing, embeddings, and storage.

### Fixed
- Add write permissions to GitHub Actions workflow
- Use grep to read version instead of Python import
- Install python-dotenv in GitHub Actions workflow

### Changed
- selected deletion


## [0.1.0] - 2026-01-08

### Added
- Smart Ingestion feature with AI-powered metadata extraction
- Real-time embedding generation with progress tracking
- Document upload to Supabase storage and database
- AI Assistant with RAG-based document search
- Session and working group management
- Organization chart visualization

### Fixed
- Windows file handle issues (Errno 22) during PDF processing
- Document type validation to match database constraints
- Embedding generation workflow with pre-extraction strategy
- Document ID extraction from Supabase responses

### Features
- **Smart Ingestion**: Upload PDFs with automatic metadata extraction (symbol, title, author, regulations)
- **Chunk Counter**: Shows number of chunks extracted (e.g., "✓ 40 chunks extracted")
- **Progress Bar**: Real-time progress during embedding generation (e.g., "Generating embedding 5/40...")
- **Editable Fields**: All metadata fields editable before saving
- **Session Linking**: Documents automatically linked to working group sessions

---

All notable changes to the UNECE WP.29 Archive project will be documented in this file.

## [1.1.0] - 2026-01-13

### Added
- **Adopted Proposals Management**: New page for tracking adopted proposals from WP.29/GR sessions
  - Upload and parse adopted proposals documents
  - Extract regulation references and proposal metadata
  - Link proposals to sessions and regulations
  - Track adoption status and implementation dates
- **RAG Storage Optimization**: Refactored chunk storage architecture
  - Moved chunk text from PostgreSQL to Supabase Storage
  - Reduced database footprint by ~75% for better scalability
  - Added parallel fetching for chunk retrieval
  - Implemented hybrid hot/cold storage strategy
  - Created migration scripts for existing data

### Changed
- Updated `embeddings` table schema with `content_path` column
- Modified ingestion logic to store chunks as JSON in Storage
- Enhanced retrieval logic with ThreadPoolExecutor for parallel downloads

### Technical
- Added `chunks_cache` Storage bucket
- Created migration script `migrate_chunks_to_storage.py`
- Added `weaviate_client.py` for future vector database scaling
- Updated config with `CHUNKS_CACHE_BUCKET` constant

## Future Versions

Future releases will be documented here.
