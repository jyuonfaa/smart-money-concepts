import pypdf
import re

def extract_video8():
    pdf_path = "ict mentorship.pdf"
    output_path = "video8_extracted_notes.txt"
    
    print(f"Extracting Video 8 (Market Maker Model) from {pdf_path}...")
    
    with open(pdf_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        text = ""
        # Video 8 typically starts after the Sovereign Liquidity Engine (Video 7)
        # Video 7 started around page 37. We'll scan from 45 onwards.
        for i in range(45, len(reader.pages)):
            page_text = reader.pages[i].extract_text()
            text += f"\n--- Page {i+1} ---\n"
            text += page_text
            
            # Stop if we hit Video 9 or another major section
            if "Video 9" in page_text or "TEACHING 9" in page_text:
                break
                
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    
    print(f"Extraction complete. Saved to {output_path}")

if __name__ == "__main__":
    extract_video8()
