import google.generativeai as genai
from config import Config
from supabase_client import SupabaseClient
import json
import os
import tempfile

# Configure Gemini
genai.configure(api_key=Config.GOOGLE_API_KEY)

class ProposalExtractor:
    
    @staticmethod
    def extract_proposals_from_doc(doc_id):
        """
        Extract adopted proposals from a given document ID.
        Returns a list of dicts: 
        [{'regulation': 'R48', 'series': '09', 'supplement': '01', 'entry_date': '2025-06-01', 'description': '...'}]
        """
        client = SupabaseClient.get_client()
        
        # 1. Fetch Document Info
        doc = client.table("documents").select("*").eq("id", doc_id).execute()
        if not doc.data:
            raise ValueError(f"Document {doc_id} not found")
        
        doc_data = doc.data[0]
        file_url = doc_data.get('file_url')
        
        if not file_url:
            raise ValueError("Document has no file URL")
            
        print(f"Processing {doc_data['symbol']}...")
        
        # 2. Download File
        # Extract path
        if Config.STORAGE_BUCKET in file_url:
            file_path = file_url.split(f'/{Config.STORAGE_BUCKET}/')[-1]
        else:
             # Try generic parse
             file_path = file_url.split('/')[-1]

        pdf_bytes = SupabaseClient.download_file(file_path)
        
        # 3. Create Temp File for Gemini 
        # (Gemini API usually accepts path or bytes depending on SDK version, 
        # but file API is best for PDFs)
        suffix = ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name
            
        try:
            # 4. Upload to Gemini File API
            # Note: For Flash, we can often pass data directly if small, or use File API.
            # Using File API is safer for reports.
            print("Uploading to Gemini...")
            sample_file = genai.upload_file(path=tmp_path, display_name=doc_data['symbol'])
            
            # 5. Generate Content
            print("Analyzing with Gemini...")
            model = genai.GenerativeModel(Config.GEMINI_FLASH_MODEL)
            
            prompt = """
            Analyze this WP.29 report/document. Identify all "Adopted Proposals" or "Amendments" to regulations.
            For each adopted proposal, extract:
            - regulation_id: The regulation number (e.g., "R48", "R13", "R129"). Format as "R" + number.
            - series: The series of amendments (e.g., "09", "04"). If not specified, null.
            - supplement: The supplement number (e.g., "12", "01").
            - entry_date: The date of entry into force. Look specifically for dates in square brackets like "[26.09.2025]" or in the "Situation of Entry into Force" column. Format as YYYY-MM-DD. If unknown/TBD, null.
            - document_code: The document symbol or number (e.g. "2025/67", "ECE/TRANS/WP.29/2025/57"). Found in "Document" column.
            - description: A concise summary of WHAT changed (e.g., "Introduces requirements for step-lighting", "Clarifies test procedure for...").
            - status: "Adopted" (default)

            Return a valid JSON list of objects.
            Example:
            [
                {"regulation_id": "R48", "series": "09", "supplement": "02", "entry_date": "2025-06-22", "description": "New requirements for AV signalling.", "status": "Adopted"}
            ]
            RETURN ONLY JSON.
            """
            
            response = model.generate_content([prompt, sample_file])
            
            # Clean up file
            # genai.delete_file(sample_file.name) # Cleanup if needed
            
            # Parse JSON
            json_text = response.text
            if json_text.startswith("```"):
                parts = json_text.split("```")
                # find json part
                for p in parts:
                    if p.strip().startswith("json"):
                        json_text = p.strip()[4:].strip()
                        break
                    elif p.strip().startswith("["):
                         json_text = p.strip()
                         break
            
            try:
                data = json.loads(json_text)
                return data
            except json.JSONDecodeError:
                print(f"Failed to parse JSON: {json_text}")
                return []
                
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

if __name__ == "__main__":
    # Test run
    # doc_id = "..."
    pass
