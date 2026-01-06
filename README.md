# UNECE WP.29 Intelligent Archive

AI-powered Document Management System for UN vehicle regulations.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GOOGLE_API_KEY=your_gemini_key
```

### 3. Initialize Database

1. Go to your Supabase dashboard → SQL Editor
2. Run the contents of `init_database.sql`
3. Run the contents of `vector_search_function.sql`

Or use the helper script:

```bash
python init_db_helper.py
```

### 4. Run the Application

```bash
streamlit run Home.py
```

## 📁 Project Structure

```
WP29_Expert/
├── app.py                    # Main Streamlit entry point
├── config.py                 # Configuration management
├── supabase_client.py        # Database operations
├── gemini_client.py          # AI operations
├── pdf_processor.py          # PDF text extraction
├── embedding_service.py      # RAG/vector search
├── init_database.sql         # Database schema
├── vector_search_function.sql # Vector search RPC
├── init_db_helper.py         # Database setup helper
└── pages/
    ├── 1_Admin_Structure.py  # Group & Session management
    ├── 2_Smart_Ingestion.py  # Document upload with AI
    ├── 3_Regulation_Library.py
    ├── 4_Search_Session.py
    ├── 5_AI_Assistant.py     # RAG chatbot
    └── 6_Report_Generator.py # AI report generation
```

## 🎯 Features

### 📚 Document Management
- Hierarchical organization (WP29 → GRs → IWGs)
- Session-based document grouping
- Smart metadata extraction with AI

### 🤖 AI-Powered
- Automatic metadata extraction from PDFs
- RAG-based document search
- Authority-ranked results (Reports > Proposals)
- AI-generated session summaries

### 🔍 Search & Discovery
- Multi-filter document search
- Session-based views
- Regulation-focused organization

### 📊 Reports
- AI-summarized session reports
- Grouped by regulation
- Export to Word/Markdown

## 🔧 Technology Stack

- **Frontend:** Streamlit
- **Database:** Supabase (PostgreSQL + pgvector)
- **AI:** Google Gemini (Flash + Pro)
- **PDF:** PyMuPDF
- **Vector Search:** pgvector with cosine similarity

## 📖 Usage Guide

### 1. Admin & Structure
- Create groups (GRE, GRVA, etc.)
- Set up sessions
- View hierarchy

### 2. Smart Ingestion
- Select group and session
- Upload PDFs (drag & drop)
- AI extracts metadata automatically
- Review and save

### 3. Regulation Library
- Upload consolidated regulations
- Track versions (In Force/Superseded)
- Manage series and revisions

### 4. Search & Session View
- Filter by group, session, regulation, type
- View outcomes (Reports/Agendas) separately
- Browse working documents

### 5. AI Assistant
- Ask questions about regulations
- RAG-powered answers with citations
- Authority-based ranking

### 6. Report Generator
- Select a session
- Generate AI summary
- Export to Word/Markdown

## 🛠️ Database Schema

### Tables
- `groups` - WP29, GRs, IWGs hierarchy
- `sessions` - Meeting sessions
- `regulations` - Abstract regulations (R48, R10, etc.)
- `regulation_versions` - Specific versions with PDFs
- `documents` - Working documents
- `embeddings` - Vector store for RAG

### Authority Levels
- **10:** Regulations & Reports (high authority)
- **1:** Proposals (low authority)

## 📝 Notes

- First run will auto-create WP29 root group
- Embeddings are optional but recommended for AI features
- Reports have higher search authority than proposals
- pgvector extension must be enabled in Supabase

## 🐛 Troubleshooting

**Database connection error:**
- Check .env file configuration
- Verify Supabase URL and key
- Ensure database schema is initialized

**Vector search not working:**
- Run `vector_search_function.sql` in Supabase
- Verify pgvector extension is enabled
- Check embeddings table has data

**AI extraction fails:**
- Verify GOOGLE_API_KEY in .env
- Check internet connection
- Try a different PDF (first page should contain metadata)

## 📄 License

This project is for UNECE WP.29 internal use.
