"""
Google Gemini API client wrapper for UNECE WP.29 Archive
Handles AI extraction, chat, and embeddings
"""
import google.generativeai as genai
from config import Config
from typing import Dict, List, Optional
import json

# Configure Gemini API
genai.configure(api_key=Config.GOOGLE_API_KEY)

class GeminiClient:
    """Google Gemini API wrapper"""
    
    @staticmethod
    def get_model():
        """Get the configured GenerativeModel instance"""
        return genai.GenerativeModel(Config.GEMINI_PRO_MODEL)
    
    @staticmethod
    def extract_metadata(text: str) -> Dict:
        """
        Extract metadata from first page of PDF using Gemini Flash
        Returns: {symbol, title, author, regulation_ref, doc_type}
        """
        model = genai.GenerativeModel(Config.GEMINI_FLASH_MODEL)
        
        prompt = f"""
You are analyzing a UNECE working document (Interpretations, Reports, or Regulations).
Extract the following metadata in JSON format:

{{{{
  "symbol": "document symbol (e.g., 'ECE/TRANS/WP.29/GRE/2024/2' or 'GRE-90-02')",
  "title": "document title",
  "author": "author/submitter (country or organization)",
  "mentioned_regulations": ["list", "of", "regulations"],
  "doc_type": "one of: Report, Agenda, Adopted Proposals, Formal, Informal"
}}}}

Guidelines:
- If the document is a session report, set doc_type to "Report"
- If it's an agenda, set doc_type to "Agenda"
- If it contains adopted proposals, set doc_type to "Adopted Proposals"
- Formal documents usually have ECE/TRANS format, Informal use group codes (e.g., GRE-90-02)

CRITICAL FOR REGULATIONS:
- Scan the ENTIRE provided text.
- Extract ALL mentioned regulations.
- For UNECE Regulations: Use format "Rxx" or "Rxx.yy" (e.g., "R48.09").
- For EU/EC Regulations/Directives: Keep the official format (e.g., "661/2009", "2007/46/EC", "EU 2018/858").
- Extract ALL mentioned regulations (e.g., "R48", "R10", "Regulation No. 13", "Reg (EC) 661/2009").
- STRICTLY use format "Rxx" or "Rxx.yy" for UN Regulations.
- Example: "Regulation No. 48" -> "R48"
- Example: "09 series of amendments to R48" -> "R48.09"
- Example: "R48-09" -> "R48.09"
- Example: "Regulation (EC) No 661/2009" -> "661/2009"
- Example: "Directive 2007/46/EC" -> "2007/46/EC"
- Treat different series of amendments as distinct items.
- If the document discusses specific regulations, list them all.
- Return an empty list [] only if absolutely no regulations are mentioned.

Here's the text:

{text}

Return ONLY the JSON object, no other text.
"""
        
        try:
            response = model.generate_content(prompt)
            json_str = response.text.strip()
            
            # Clean up markdown code blocks that Gemini often adds
            # Remove ```json ... ``` or ``` ... ```
            if json_str.startswith("```"):
                # Split by ``` and get the middle part
                parts = json_str.split("```")
                if len(parts) >= 3:
                    json_str = parts[1]
                elif len(parts) == 2:
                    json_str = parts[1]
                
                # Remove language identifier if present (e.g., "json")
                if json_str.strip().startswith("json"):
                    json_str = json_str.strip()[4:].strip()
            
            # Final cleanup
            json_str = json_str.strip()
            
            if not json_str:
                raise ValueError("Empty response from Gemini")
            
            metadata = json.loads(json_str)
            
            # Validate required fields
            if not isinstance(metadata, dict):
                raise ValueError("Response is not a JSON object")
            
            return metadata
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing error: {str(e)}\nResponse was: {response.text[:200]}"
            print(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Metadata extraction failed: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    @staticmethod
    def generate_embedding(text: str) -> List[float]:
        """Generate embedding vector for text using Gemini embedding model"""
        try:
            result = genai.embed_content(
                model=Config.GEMINI_EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * 768  # Return zero vector on error
    
    @staticmethod
    def generate_query_embedding(query: str) -> List[float]:
        """Generate embedding vector for search query"""
        try:
            result = genai.embed_content(
                model=Config.GEMINI_EMBEDDING_MODEL,
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return [0.0] * 768
    
    @staticmethod
    def chat_with_context(query: str, context_chunks: List[Dict]) -> str:
        """
        Generate answer using Gemini Pro with RAG context
        context_chunks: List of {content_chunk, source_id, source_type, ...}
        """
        model = genai.GenerativeModel(Config.GEMINI_PRO_MODEL)
        
        # Build context from chunks with source type
        context_parts = []
        for chunk in context_chunks:
            s_type = chunk.get('source_type', 'unknown').upper()
            symbol = chunk.get('symbol', 'Unknown')
            content = chunk['content_chunk']
            context_parts.append(f"[SOURCE: {s_type} | DOC: {symbol}]\n{content}")
            
        context = "\n\n".join(context_parts)
        
        prompt = f"""
You are an expert assistant for UNECE WP.29 vehicle regulations.
Answer the user's question based on the following context.

IMPORTANT STRUCTURING RULES:
1.  **Divide your answer into two distinct sections**:
    *   **🏛️ Official Regulations & Documents**: Use information from sources marked as 'DOCUMENT' or 'REGULATION'.
    *   **💡 Interpretations**: Use information from sources marked as 'INTERPRETATION'.
2.  **Explicitly state if a section has no information** (e.g., "No interpretations found for this topic.").
3.  **Always cite the document symbol** (e.g., R48.09, 2018/858) when referencing information.
4.  **Answer in the same language as the User Question** (if Italian, answer in Italian).

Context:
{context}

User Question: {query}

Answer:
"""
        
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {e}"

    @staticmethod
    def optimize_query(query: str) -> str:
        """
        Extracts powerful search keywords from the user's query.
        Prioritizes technical terms and synonyms in multiple languages.
        """
        model = genai.GenerativeModel(Config.GEMINI_FLASH_MODEL)
        prompt = f"""You are a search query optimizer for a database of:
1. UN Vehicle Regulations (mostly English)
2. Type Approval Authority Meeting (TAAM) Interpretations (English, German, French)
3. Working documents from UNECE sessions (Formal/Informal proposals)

Your task: Extract the MOST RELEVANT KEYWORDS from the user's query.

CRITICAL RULES:
1. Output ONLY keywords and technical terms, separated by spaces.
2. DO NOT output full sentences or questions.
3. Include English translations of any non-English terms.
4. Include German conceptual translations for specific automotive terms (e.g. "Single Vehicle Approval" -> "Einzelgenehmigung").
5. Include Spanish technical terms if relevant to the query context.
6. TARGET LANGUAGES: English, German, Italian, Spanish.


EXAMPLES:
- "che documenti trovi sui loghi?" -> "logo logos trademark brand Marke Warenzeichen manufacturer marking"
- "omologazione individuale" -> "individual approval Einzelgenehmigung type-approval IVA"
- "pedestrian protection requirements" -> "pedestrian protection Fußgängerschutz bumper front end R127"
- "luces de carretera" -> "driving beam headlamp fernlicht R48 R112"
- "documenti della sessione 91 del GRE" -> "GRE session 91 GRE-91"

User Query: "{query}"
Keywords:
"""
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return query # Fallback to original

    
    @staticmethod
    def summarize_session(documents: List[Dict]) -> str:
        """
        Summarize session documents grouped by regulation using Gemini Pro
        documents: List of document metadata with content
        """
        model = genai.GenerativeModel(Config.GEMINI_PRO_MODEL)
        
        # Group documents by regulation
        by_regulation = {}
        for doc in documents:
            reg_ref = doc.get('regulation_ref_id', 'General')
            if reg_ref not in by_regulation:
                by_regulation[reg_ref] = []
            by_regulation[reg_ref].append(doc)
        
        # Build summary for each regulation
        summaries = []
        for reg_id, docs in by_regulation.items():
            doc_list = "\n".join([
                f"- {doc['symbol']}: {doc['title']}"
                for doc in docs
            ])
            
            prompt = f"""
Summarize the key discussions and decisions for regulation {reg_id} based on these documents:

{doc_list}

Provide a concise summary of the main topics, proposals, and outcomes.
"""
            
            try:
                response = model.generate_content(prompt)
                summaries.append(f"## {reg_id}\n\n{response.text}\n")
            except Exception as e:
                summaries.append(f"## {reg_id}\n\nError generating summary: {e}\n")
        
        return "\n".join(summaries)
