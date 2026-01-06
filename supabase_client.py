"""
Supabase client wrapper for UNECE WP.29 Archive
Provides database and storage operations
"""
from supabase import create_client, Client
from config import Config
from typing import Optional, List, Dict, Any
from datetime import datetime

class SupabaseClient:
    """Singleton Supabase client"""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client instance"""
        if cls._instance is None:
            cls._instance = create_client(
                Config.SUPABASE_URL,
                Config.SUPABASE_KEY
            )
        return cls._instance
    
    # =========================================================================
    # GROUPS
    # =========================================================================
    
    @staticmethod
    def get_all_groups() -> List[Dict]:
        """Get all groups"""
        client = SupabaseClient.get_client()
        response = client.table("groups").select("*").execute()
        return response.data
    
    @staticmethod
    def create_group(group_id: str, full_name: str, group_type: str, 
                     parent_id: Optional[str] = None) -> Dict:
        """Create a new group"""
        client = SupabaseClient.get_client()
        data = {
            "id": group_id,
            "full_name": full_name,
            "type": group_type,
            "parent_group_id": parent_id
        }
        response = client.table("groups").insert(data).execute()
        return response.data[0] if response.data else {}
    
    @staticmethod
    def get_group(group_id: str) -> Optional[Dict]:
        """Get a specific group"""
        client = SupabaseClient.get_client()
        response = client.table("groups").select("*").eq("id", group_id).execute()
        return response.data[0] if response.data else None
    
    # =========================================================================
    # SESSIONS
    # =========================================================================
    
    @staticmethod
    def get_sessions_by_group(group_id: str) -> List[Dict]:
        """Get all sessions for a group"""
        client = SupabaseClient.get_client()
        response = client.table("sessions").select("*").eq("group_id", group_id).execute()
        return response.data
    
    @staticmethod
    def create_session(group_id: str, code: str, year: int, 
                       dates: Optional[str] = None) -> Dict:
        """Create a new session"""
        client = SupabaseClient.get_client()
        data = {
            "group_id": group_id,
            "code": code,
            "year": year,
            "dates": dates
        }
        response = client.table("sessions").insert(data).execute()
        return response.data[0] if response.data else {}
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Dict]:
        """Get a specific session"""
        client = SupabaseClient.get_client()
        response = client.table("sessions").select("*").eq("id", session_id).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def update_session(session_id: str, code: str, year: int, group_id: str, dates: Optional[str] = None) -> Dict:
        """Update an existing session"""
        client = SupabaseClient.get_client()
        data = {
            "group_id": group_id,
            "code": code,
            "year": year,
            "dates": dates
        }
        response = client.table("sessions").update(data).eq("id", session_id).execute()
        return response.data[0] if response.data else {}
    
    # =========================================================================
    # REGULATIONS
    # =========================================================================
    
    @staticmethod
    def get_all_regulations() -> List[Dict]:
        """Get all regulations"""
        client = SupabaseClient.get_client()
        response = client.table("regulations").select("*").execute()
        return response.data
    
    @staticmethod
    def create_regulation(reg_id: str, title: str, topic: Optional[str] = None) -> Dict:
        """Create a new regulation"""
        client = SupabaseClient.get_client()
        data = {
            "id": reg_id,
            "title": title,
            "topic": topic
        }
        response = client.table("regulations").insert(data).execute()
        return response.data[0] if response.data else {}
    
    @staticmethod
    def create_regulation_version(regulation_id: str, series: str, revision: str,
                                  status: str, entry_date: str, file_url: str) -> Dict:
        """Create a regulation version"""
        client = SupabaseClient.get_client()
        data = {
            "regulation_id": regulation_id,
            "series": series,
            "revision": revision,
            "status": status,
            "entry_date": entry_date,
            "file_url": file_url
        }
        response = client.table("regulation_versions").insert(data).execute()
        return response.data[0] if response.data else {}
    
    @staticmethod
    def get_regulation_versions(regulation_id: str) -> List[Dict]:
        """Get all versions of a regulation"""
        client = SupabaseClient.get_client()
        response = client.table("regulation_versions").select("*").eq(
            "regulation_id", regulation_id
        ).execute()
        return response.data
    
    # =========================================================================
    # DOCUMENTS
    # =========================================================================
    
    @staticmethod
    def create_document(session_id: str, symbol: str, title: str, author: str,
                       doc_type: str, regulation_ref_id: Optional[str] = None,
                       regulation_mentioned: Optional[str] = None,
                       file_url: Optional[str] = None, submission_date: Optional[str] = None) -> Dict:
        """Create a new document"""
        client = SupabaseClient.get_client()
        data = {
            "session_id": session_id,
            "symbol": symbol,
            "title": title,
            "author": author,
            "doc_type": doc_type,
            "regulation_ref_id": regulation_ref_id,
            "regulation_mentioned": regulation_mentioned,
            "file_url": file_url,
            "submission_date": submission_date
        }
        response = client.table("documents").insert(data).execute()
        return response.data[0] if response.data else {}
    
    @staticmethod
    def get_documents_by_session(session_id: str) -> List[Dict]:
        """Get all documents for a session"""
        client = SupabaseClient.get_client()
        response = client.table("documents").select("*").eq("session_id", session_id).execute()
        return response.data
    
    @staticmethod
    def get_all_documents() -> List[Dict]:
        """Get all documents in the database"""
        client = SupabaseClient.get_client()
        # Fetch essential fields
        response = client.table("documents").select("*").execute()
        return response.data
    
    @staticmethod
    def search_documents(filters: Dict[str, Any]) -> List[Dict]:
        """Search documents with multiple filters"""
        client = SupabaseClient.get_client()
        query = client.table("documents").select("*, sessions!inner(group_id, code, year)")
        
        if "session_id" in filters:
            query = query.eq("session_id", filters["session_id"])
        if "doc_type" in filters:
            query = query.eq("doc_type", filters["doc_type"])
        if "regulation_ref_id" in filters:
            query = query.eq("regulation_ref_id", filters["regulation_ref_id"])
        if "year" in filters:
            # Filter on joined column
            query = query.eq("sessions.year", filters["year"])
        
        response = query.execute()
        return response.data

    @staticmethod
    def get_documents_without_embeddings() -> List[Dict]:
        """Find documents that don't have embeddings generated yet"""
        client = SupabaseClient.get_client()
        
        # 1. Get all documents
        docs_response = client.table("documents").select("id, file_url, doc_type, symbol, title, sessions(group_id, year, code)").execute()
        all_docs = docs_response.data
        
        if not all_docs:
            return []
            
        # 2. Get all embedding source IDs
        # Note: This might be heavy if table is huge, better to use a left join RPC if possible,
        # but for now client-side diff is fine for reasonable dataset size.
        emb_response = client.table("embeddings").select("source_id", count="exact").execute()
        existing_embedding_ids = {e['source_id'] for e in emb_response.data}
        
        # 3. Find missing
        missing_docs = [d for d in all_docs if d['id'] not in existing_embedding_ids]
        return missing_docs
    
    # =========================================================================
    # EMBEDDINGS
    # =========================================================================
    
    @staticmethod
    def create_embedding(source_id: str, source_type: str, content_chunk: str,
                        embedding: List[float], authority_level: int) -> Dict:
        """Create an embedding record"""
        client = SupabaseClient.get_client()
        data = {
            "source_id": source_id,
            "source_type": source_type,
            "content_chunk": content_chunk,
            "embedding": embedding,
            "authority_level": authority_level
        }
        response = client.table("embeddings").insert(data).execute()
        return response.data[0] if response.data else {}
    
    @staticmethod
    def search_embeddings(query_embedding: List[float], limit: int = 10) -> List[Dict]:
        """Search embeddings using vector similarity"""
        client = SupabaseClient.get_client()
        # Use RPC for vector similarity search
        response = client.rpc(
            "match_embeddings",
            {
                "query_embedding": query_embedding,
                "match_count": limit,
                "filter_min_similarity": 0.01 # Lower threshold to capture interpretations
            }
        ).execute()
        return response.data
    
    # =========================================================================
    # STORAGE
    # =========================================================================
    
    @staticmethod
    def upload_file(file_path: str, file_bytes: bytes) -> str:
        """Upload file to Supabase storage and return public URL"""
        client = SupabaseClient.get_client()
        
        # Upload to storage with correct MIME type and content-disposition
        response = client.storage.from_(Config.STORAGE_BUCKET).upload(
            file_path,
            file_bytes,
            file_options={
                "content-type": "application/pdf",
                "cache-control": "public, max-age=3600",
                "content-disposition": "inline",  # Tell browser to display inline
                "upsert": "true"
            }
        )
        
        # Get public URL
        public_url = client.storage.from_(Config.STORAGE_BUCKET).get_public_url(file_path)
        return public_url
        
    @staticmethod
    def get_public_url(path_or_url: str) -> str:
        """Get public URL from path or return URL if already full"""
        if not path_or_url:
            return ""
        if path_or_url.startswith("http"):
            return path_or_url
        
        client = SupabaseClient.get_client()
        try:
            return client.storage.from_(Config.STORAGE_BUCKET).get_public_url(path_or_url)
        except Exception:
            return path_or_url
    
    @staticmethod
    def download_file(file_path: str) -> bytes:
        """Download file from Supabase storage"""
        client = SupabaseClient.get_client()
        response = client.storage.from_(Config.STORAGE_BUCKET).download(file_path)
        return response
    
    @staticmethod
    def delete_file(file_url: str) -> bool:
        """
        Delete file from Supabase storage given its public URL.
        Returns True if deletion was successful, False otherwise.
        """
        try:
            client = SupabaseClient.get_client()
            # Extract file path from URL
            # URL format: https://.../storage/v1/object/public/unece-archive/path/to/file.pdf
            file_path = file_url.split(f'/{Config.STORAGE_BUCKET}/')[-1]
            client.storage.from_(Config.STORAGE_BUCKET).remove([file_path])
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_signed_url(file_url: str, expires_in: int = 86400) -> str:
        """
        Get a signed URL for a file given its public URL.
        Signed URLs work better with Adobe Acrobat and provide better security.
        
        Args:
            file_url: The public URL of the file
            expires_in: Expiration time in seconds (default: 86400 = 24 hours)
        
        Returns:
            Signed URL string
        """
        try:
            client = SupabaseClient.get_client()
            # Extract file path from URL
            file_path = file_url.split(f'/{Config.STORAGE_BUCKET}/')[-1]
            
            # Create signed URL with proper headers
            response = client.storage.from_(Config.STORAGE_BUCKET).create_signed_url(
                file_path, 
                expires_in,
                options={
                    "download": False  # Don't force download, allow inline viewing
                }
            )
            
            # Response format: {'signedURL': '...', 'signedUrl': '...'}
            return response.get('signedURL') or response.get('signedUrl', file_url)
        except Exception:
            # Fallback to public URL if signed URL fails
            return file_url
    # =========================================================================
    # INTERPRETATIONS & ISSUERS
    # =========================================================================

    @staticmethod
    def get_all_issuers() -> List[Dict]:
        """Get all interpretation issuers"""
        client = SupabaseClient.get_client()
        response = client.table("issuers").select("*").execute()
        return response.data

    @staticmethod
    def create_issuer(name: str, code: str, i_type: str) -> Dict:
        """Create a new issuer"""
        client = SupabaseClient.get_client()
        data = {"name": name, "code": code, "type": i_type}
        response = client.table("issuers").insert(data).execute()
        return response.data[0] if response.data else {}

    @staticmethod
    def create_interpretation(
        title: str, issuer_id: str, issue_date: str, status: str,
        regulation_mentioned: Optional[str] = None,
        comments: Optional[str] = None,
        content_text: Optional[str] = None,
        file_url: Optional[str] = None,
        is_public: bool = False,
        session_id: Optional[str] = None
    ) -> Dict:
        """Create a new interpretation record"""
        client = SupabaseClient.get_client()
        data = {
            "title": title,
            "issuer_id": issuer_id,
            "issue_date": issue_date,
            "status": status,
            "regulation_mentioned": regulation_mentioned,
            "comments": comments,
            "content_text": content_text,
            "file_url": file_url,
            "is_public": is_public,
            "session_id": session_id
        }
        response = client.table("interpretations").insert(data).execute()
        return response.data[0] if response.data else {}

    @staticmethod
    def update_interpretation(
        interp_id: str,
        title: Optional[str] = None,
        issuer_id: Optional[str] = None,
        issue_date: Optional[str] = None,
        status: Optional[str] = None,
        regulation_mentioned: Optional[str] = None,
        comments: Optional[str] = None,
        is_public: Optional[bool] = None
    ) -> Dict:
        """Update an existing interpretation"""
        client = SupabaseClient.get_client()
        data = {}
        if title is not None: data['title'] = title
        if issuer_id is not None: data['issuer_id'] = issuer_id
        if issue_date is not None: data['issue_date'] = issue_date
        if status is not None: data['status'] = status
        if regulation_mentioned is not None: data['regulation_mentioned'] = regulation_mentioned
        if comments is not None: data['comments'] = comments
        if is_public is not None: data['is_public'] = is_public
        
        if not data:
            return {}
            
        response = client.table("interpretations").update(data).eq("id", interp_id).execute()
        return response.data[0] if response.data else {}

    @staticmethod
    def delete_interpretation(interp_id: str) -> bool:
        """
        Delete an interpretation and its associated file.
        Returns True if successful.
        """
        client = SupabaseClient.get_client()
        
        # 1. Get file URL first to delete from storage
        try:
            res = client.table("interpretations").select("file_url").eq("id", interp_id).execute()
            if res.data and res.data[0].get('file_url'):
                SupabaseClient.delete_file(res.data[0]['file_url'])
        except Exception as e:
            print(f"Error deleting file for interpretation {interp_id}: {e}")
            # Continue to delete record anyway
            
        # 2. Delete Embeddings (Manual cascade)
        try:
            client.table("embeddings").delete().eq("source_id", interp_id).execute()
        except Exception as e:
            print(f"Error deleting embeddings for {interp_id}: {e}")

        # 3. Delete DB record
        try:
            client.table("interpretations").delete().eq("id", interp_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting interpretation record: {e}")
            return False

    @staticmethod
    def get_interpretations(include_private: bool = False) -> List[Dict]:
        """Get interpretations based on visibility"""
        client = SupabaseClient.get_client()
        query = client.table("interpretations").select("*, issuers(name, code)")
        
        # Note: RLS handles security on the DB side, 
        # but if we are using a SERVICE key in .env, we see everything.
        # So we might need to filter client-side if we are pretending to be a user.
        # For now, let's assume the DB returns what we are allowed to see.
        
        if not include_private:
             query = query.eq("is_public", True)
             
        response = query.order("issue_date", desc=True).execute()
        return response.data

    @staticmethod
    def get_user_role(user_id: str) -> str:
        """Get user role from profiles"""
        client = SupabaseClient.get_client()
        try:
            # print(f"DEBUG: Fetching role for {user_id}")
            response = client.table("profiles").select("role").eq("id", user_id).execute()
            # print(f"DEBUG: Role response: {response.data}")
            if response.data:
                return response.data[0]['role']
        except Exception as e:
            print(f"DEBUG: Error fetching role: {e}")
            pass
        return 'basic'  # Default fallback

    @staticmethod
    def get_all_profiles() -> List[Dict]:
        """Get all user profiles (Admin only)"""
        client = SupabaseClient.get_client()
        # Let exceptions bubble up to be handled by the UI
        response = client.table("profiles").select("*").order("created_at", desc=True).execute()
        return response.data if response.data else []

    @staticmethod
    def update_user_role(user_id: str, new_role: str) -> bool:
        """Update a user's role (Admin only)"""
        client = SupabaseClient.get_client()
        try:
            response = client.table("profiles").update({"role": new_role}).eq("id", user_id).execute()
            return True if response.data else False
        except Exception as e:
            print(f"Error updating role: {e}")
            return False

    @staticmethod
    def get_admin_client() -> Client:
        """Get Supabase client with Service Role (Admin privileges)"""
        if not Config.SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_SERVICE_KEY not found in .env")
            
        return create_client(
            Config.SUPABASE_URL,
            Config.SUPABASE_SERVICE_KEY
        )

    @staticmethod
    def create_user(email: str, password: str, full_name: str) -> bool:
        """Create a new user using Admin API"""
        # Exceptions will be caught by the UI
        admin_client = SupabaseClient.get_admin_client()
        response = admin_client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True, # Auto-confirm
            "user_metadata": {"full_name": full_name}
        })
        return True if response.user else False

    @staticmethod
    def delete_user(user_id: str) -> bool:
        """Delete a user using Admin API"""
        # Exceptions will be caught by the UI
        admin_client = SupabaseClient.get_admin_client()
        response = admin_client.auth.admin.delete_user(user_id)
        return True
