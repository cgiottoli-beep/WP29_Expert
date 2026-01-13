"""
Embedding service for RAG (Retrieval Augmented Generation)
Handles embedding generation and vector search
"""
from typing import List, Dict, Optional
from gemini_client import GeminiClient
from supabase_client import SupabaseClient
from pdf_processor import PDFProcessor

class EmbeddingService:
    """Service for managing embeddings and vector search"""
    
    @staticmethod
    def generate_document_embeddings(document_id: str, pdf_bytes: bytes, 
                                     doc_type: str, progress_callback=None) -> int:
        """
        Generate and store embeddings for a document
        Optional progress_callback(current, total)
        """
        # Determine authority level based on doc_type
        authority_level = 10 if doc_type in ['Report', 'Agenda'] else 1
        
        # Extract and chunk text
        chunks = PDFProcessor.extract_chunks(pdf_bytes, chunk_size=1000)
        
        if not chunks:
            return 0
        
        total_chunks = len(chunks)
        embeddings_created = 0
        
        for i, chunk in enumerate(chunks):
            # Report progress
            if progress_callback:
                progress_callback(i + 1, total_chunks)
                
            if not chunk.strip():
                continue
            
            # Generate embedding
            try:
                embedding = GeminiClient.generate_embedding(chunk)
            except Exception as e:
                print(f"Error generating embedding API call: {e}")
                continue
            
            # NEW: Upload chunk to Storage instead of saving in DB
            try:
                # Create JSON payload
                chunk_data = {
                    "text": chunk,
                    "source_id": document_id,
                    "source_type": "document",
                    "chunk_index": i,
                    "authority_level": authority_level
                }
                
                # Upload to chunks_cache bucket
                storage_path = f"{document_id}/chunk_{i}.json"
                SupabaseClient.upload_json(storage_path, chunk_data)
                
                # Store embedding in DB with path reference
                SupabaseClient.create_embedding(
                    source_id=document_id,
                    source_type="document",
                    embedding=embedding,
                    authority_level=authority_level,
                    content_path=storage_path
                )
                embeddings_created += 1
            except Exception as e:
                print(f"Error storing embedding: {e}")
        
        return embeddings_created
    
    @staticmethod
    def generate_regulation_embeddings(regulation_version_id: str, 
                                       pdf_bytes: bytes) -> int:
        """
        Generate and store embeddings for a regulation version
        Regulations always have highest authority (10)
        """
        chunks = PDFProcessor.extract_chunks(pdf_bytes, chunk_size=1000)
        
        embeddings_created = 0
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            
            embedding = GeminiClient.generate_embedding(chunk)
            
            try:
                # Create JSON payload
                chunk_data = {
                    "text": chunk,
                    "source_id": regulation_version_id,
                    "source_type": "regulation",
                    "chunk_index": i,
                    "authority_level": 10
                }
                
                # Upload to chunks_cache bucket
                storage_path = f"{regulation_version_id}/chunk_{i}.json"
                SupabaseClient.upload_json(storage_path, chunk_data)
                
                # Store embedding in DB with path reference
                SupabaseClient.create_embedding(
                    source_id=regulation_version_id,
                    source_type="regulation",
                    embedding=embedding,
                    authority_level=10,  # Regulations have highest authority
                    content_path=storage_path
                )
                embeddings_created += 1
            except Exception as e:
                print(f"Error storing regulation embedding: {e}")
        
        return embeddings_created
    
    @staticmethod
    def search_with_reranking(query: str, limit: int = 10) -> List[Dict]:
        """
        Search embeddings with authority-based re-ranking
        
        1. Generate query embedding
        2. Find similar vectors
        3. Re-rank by authority_level
        
        Returns list of chunks with metadata
        """
        # 1. Optimize query for search (Translate to English if needed)
        # This is critical for cross-lingual retrieval against English documents
        search_query = GeminiClient.optimize_query(query)
        print(f"DEBUG: Original query: '{query}' -> Search query: '{search_query}'")
        
        # 2. Generate query embedding using the optimized English query
        query_embedding = GeminiClient.generate_query_embedding(search_query)
        
        # Search using the English vector
        # Fetch more candidates to allow for effective re-ranking
        results = EmbeddingService._vector_search(query_embedding, limit * 5)
        
        # NEW: Fetch chunk content from Storage for results that don't have it in DB
        results_with_content = EmbeddingService._populate_chunk_content(results)
        
        # Re-rank by authority level (higher authority first)
        # Then by similarity score
        ranked_results = sorted(
            results_with_content,
            key=lambda x: (x.get('authority_level', 0), x.get('similarity', 0)),
            reverse=True
        )
        
        return ranked_results[:limit]
    
    @staticmethod
    def _populate_chunk_content(results: List[Dict]) -> List[Dict]:
        """
        Populate content_chunk field from Storage for results that need it.
        Uses parallel fetching for performance.
        
        Args:
            results: List of search results with content_path or content_chunk
            
        Returns:
            Results with content_chunk populated
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Identify which results need content fetching
        to_fetch = []
        for result in results:
            # If content_chunk is missing but content_path exists, we need to fetch
            if not result.get('content_chunk') and result.get('content_path'):
                to_fetch.append(result)
        
        # Fetch in parallel if needed
        if to_fetch:
            def fetch_content(result: Dict) -> Dict:
                """Fetch content from Storage for a single result"""
                try:
                    chunk_data = SupabaseClient.download_json(result['content_path'])
                    result['content_chunk'] = chunk_data.get('text', '')
                except Exception as e:
                    print(f"Error fetching chunk from storage: {e}")
                    result['content_chunk'] = f"[Error loading content: {e}]"
                return result
            
            # Use ThreadPoolExecutor for parallel downloads (max 10 concurrent)
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_result = {executor.submit(fetch_content, r): r for r in to_fetch}
                for future in as_completed(future_to_result):
                    # Results are updated in-place, just wait for completion
                    future.result()
        
        return results
    
    @staticmethod
    def generate_interpretation_embeddings(interpretation_id: str, 
                                           text_content: Optional[str] = None,
                                           pdf_bytes: Optional[bytes] = None,
                                           progress_callback=None) -> tuple[int, Optional[str]]:
        """
        Generate and store embeddings for an interpretation.
        Returns (count, last_error_message)
        """
        chunks = []
        
        # 1. Extract text
        if text_content:
            # Use provided text directly
            import textwrap
            paragraphs = text_content.split('\n\n')
            for p in paragraphs:
                if len(p) > 1000:
                    chunks.extend(textwrap.wrap(p, 1000))
                else:
                    chunks.append(p)
        elif pdf_bytes:
            # Extract from PDF
            try:
                chunks = PDFProcessor.extract_chunks(pdf_bytes, chunk_size=1000)
            except Exception as e:
                return 0, f"PDF extraction error: {str(e)}"
        
        if not chunks:
            return 0, "No text chunks extracted from PDF"
            
        embeddings_created = 0
        total_chunks = len(chunks)
        last_error = None
        
        for i, chunk in enumerate(chunks):
            # Report progress
            if progress_callback:
                progress_callback(i + 1, total_chunks)
                
            if not chunk.strip():
                continue
            
            try:
                embedding = GeminiClient.generate_embedding(chunk)
                
                # Create JSON payload
                chunk_data = {
                    "text": chunk,
                    "source_id": interpretation_id,
                    "source_type": "interpretation",
                    "chunk_index": i,
                    "authority_level": 12
                }
                
                # Upload to chunks_cache bucket
                storage_path = f"{interpretation_id}/chunk_{i}.json"
                SupabaseClient.upload_json(storage_path, chunk_data)
                
                # Store embedding in DB with path reference
                SupabaseClient.create_embedding(
                    source_id=interpretation_id,
                    source_type="interpretation",
                    embedding=embedding,
                    authority_level=12,  # Higher than Regulation (10) to prioritize interpretations
                    content_path=storage_path
                )
                embeddings_created += 1
            except Exception as e:
                last_error = str(e)
                print(f"Error generating/storing embedding: {e}")
                
        return embeddings_created, last_error

    @staticmethod
    def _vector_search(query_embedding: List[float], limit: int) -> List[Dict]:
        """
        Perform vector similarity search
        Note: This requires a custom RPC function in Supabase
        """
        try:
            # This will call the RPC function we'll create
            results = SupabaseClient.search_embeddings(query_embedding, limit)
            return results
        except Exception as e:
            print(f"Error in vector search: {e}")
            # Fallback: return empty list
            return []
