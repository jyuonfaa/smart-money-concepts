import pypdf
import sys

def extract_ict_sections(pdf_path, keywords):
    reader = pypdf.PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"Scanning {total_pages} pages for {keywords}...")
    
    findings = []
    for i in range(total_pages):
        text = reader.pages[i].extract_text()
        if any(kw.lower() in text.lower() for kw in keywords):
            findings.append(f"--- PAGE {i+1} ---\n{text}\n")
            
    return findings

if __name__ == "__main__":
    pdf_file = "ict mentorship.pdf"
    target_keywords = ["Video 7", "Video 8", "Market Maker", "MMSM", "MMBM"]
    
    try:
        sections = extract_ict_sections(pdf_file, target_keywords)
        if not sections:
            print("No matching sections found.")
        else:
            with open("video7_extracted_notes.txt", "w", encoding="utf-8") as f:
                for s in sections:
                    f.write(s)
            print(f"Extracted {len(sections)} pages to video7_extracted_notes.txt")
    except Exception as e:
        print(f"Error: {e}")
