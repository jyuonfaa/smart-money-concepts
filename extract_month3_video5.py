import PyPDF2

def extract_pages(pdf_path, start_page, end_page, output_txt):
    print(f"Extracting pages {start_page} to {end_page} from {pdf_path}...")
    
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        
        # PyPDF2 is 0-indexed, so page 1 is index 0.
        # But we want to ensure we capture the full range exactly as numbered in the PDF.
        for i in range(start_page - 1, end_page):
            try:
                page = reader.pages[i]
                text += f"\n\n--- PAGE {i+1} ---\n\n"
                text += page.extract_text()
            except Exception as e:
                print(f"Error on page {i+1}: {e}")
                
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(text)
        
    print(f"Saved extracted text to {output_txt}")

if __name__ == "__main__":
    # Video 5: Pages 216 to 226
    extract_pages('ict mentorship.pdf', 216, 226, 'month3_video5_raw.txt')
