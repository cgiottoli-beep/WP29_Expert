"""
PDF processing utilities for UNECE WP.29 Archive
Text extraction and chunking using PyMuPDF (fitz)
"""
import fitz  # PyMuPDF
from typing import List
import io

class PDFProcessor:
    """PDF text extraction and processing"""
    
    @staticmethod
    def extract_first_page(pdf_bytes: bytes) -> str:
        """
        Extract text from the first page of a PDF
        Used for metadata extraction
        Returns empty string on error
        """
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if len(doc) == 0:
                doc.close()
                raise ValueError("PDF has no pages")
            
            first_page = doc[0]
            text = first_page.get_text()
            doc.close()
            
            if not text or not text.strip():
                raise ValueError("First page contains no text")
            
            return text
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    @staticmethod
    def extract_all_text(pdf_bytes: bytes) -> str:
        """
        Extract all text from a PDF
        """
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_parts.append(page.get_text())
            
            doc.close()
            return "\n\n".join(text_parts)
        except Exception as e:
            raise Exception(f"PDF text extraction failed: {str(e)}")
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for embedding
        
        Args:
            text: Full text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks
        """
        if not text:
            return []
        
        # Ensure overlap is smaller than chunk_size to build progress
        if overlap >= chunk_size:
            overlap = chunk_size // 2

        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            
            # Try to break at a sentence or paragraph boundary
            if end < text_length:
                # Look for paragraph break first
                paragraph_break = text.rfind('\n\n', start, end)
                if paragraph_break != -1 and paragraph_break > start + overlap:
                    end = paragraph_break
                else:
                    # Look for sentence break
                    sentence_break = text.rfind('. ', start, end)
                    if sentence_break != -1 and sentence_break > start + overlap:
                        end = sentence_break + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            # Ensure we always advance at least 1 character to avoid infinite loops
            new_start = end - overlap if end < text_length else text_length
            if new_start <= start and start < text_length:
                new_start = start + 1
            start = new_start
        
        return chunks
    
    @staticmethod
    def extract_chunks(pdf_bytes: bytes, chunk_size: int = 1000) -> List[str]:
        """
        Extract and chunk PDF text in one operation
        """
        full_text = PDFProcessor.extract_all_text(pdf_bytes)
        return PDFProcessor.chunk_text(full_text, chunk_size)
    
    @staticmethod
    def get_page_count(pdf_bytes: bytes) -> int:
        """Get number of pages in PDF"""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            print(f"Error getting page count: {e}")
            return 0
