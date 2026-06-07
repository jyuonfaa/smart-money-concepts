import PyPDF2
import os

pdf_path = "ict mentorship.pdf"
output_path = "month3_video3_extracted.txt"

start_page = 180
end_page = 199

try:
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        
        extracted_text = ""
        
        # PyPDF2 is 0-indexed, so page 180 is index 179
        for page_num in range(start_page - 1, min(end_page, len(reader.pages))):
            page = reader.pages[page_num]
            text = page.extract_text()
            if text:
                extracted_text += f"\n--- Page {page_num + 1} ---\n\n"
                extracted_text += text
                
        with open(output_path, "w", encoding="utf-8") as out_file:
            out_file.write(extracted_text)
            
        print(f"Successfully extracted {len(extracted_text)} characters from pages {start_page} to {end_page}.")
        print(f"Saved to {output_path}")
except Exception as e:
    print(f"Error extracting PDF: {e}")
