
import os
import io
import fitz  # PyMuPDF
from pdf_processor import PDFProcessor

def test_extraction():
    print("="*60)
    print("TESTING PDF EXTRACTION LOGIC")
    print("="*60)

    # create a dummy PDF in memory
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello World! This is a test document for chunking.\n" * 20)
    pdf_bytes = doc.tobytes()
    doc.close()
    
    print(f"Created in-memory PDF of size: {len(pdf_bytes)} bytes")
    
    try:
        # Test extract_first_page
        text1 = PDFProcessor.extract_first_page(pdf_bytes)
        print(f"\n[extract_first_page] Success! Length: {len(text1)}")
        
        # Test extract_all_text
        text_all = PDFProcessor.extract_all_text(pdf_bytes)
        print(f"[extract_all_text] Success! Length: {len(text_all)}")
        
        # Test extract_chunks
        chunks = PDFProcessor.extract_chunks(pdf_bytes)
        print(f"[extract_chunks] Success! Chunks: {len(chunks)}")
        for i, c in enumerate(chunks[:3]):
            print(f"  Chunk {i}: {len(c)} chars - '{c[:30]}...'")
            
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extraction()
