import PyPDF2
import sys

def extract_pages(pdf_path, start_page, end_page, output_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            # Note: PyPDF2 is 0-indexed, so page 227 is index 226
            start_index = start_page - 1
            end_index = min(end_page, len(reader.pages))
            
            text_content = []
            for i in range(start_index, end_index):
                page = reader.pages[i]
                text_content.append(f"--- Page {i+1} ---")
                text_content.append(page.extract_text())
                
            with open(output_path, 'w', encoding='utf-8') as out_file:
                out_file.write("\n".join(text_content))
                
            print(f"Successfully extracted {end_index - start_index} pages to {output_path}")
            
    except Exception as e:
        print(f"Error reading PDF with PyPDF2: {e}")
        try:
            # Fallback to PyMuPDF if available
            import fitz
            doc = fitz.open(pdf_path)
            text_content = []
            for i in range(start_page - 1, end_page):
                page = doc.load_page(i)
                text_content.append(f"--- Page {i+1} ---")
                text_content.append(page.get_text())
            with open(output_path, 'w', encoding='utf-8') as out_file:
                out_file.write("\n".join(text_content))
            print(f"Successfully extracted {end_page - start_page + 1} pages using PyMuPDF to {output_path}")
        except Exception as e2:
            print(f"Error reading PDF with PyMuPDF: {e2}")

if __name__ == '__main__':
    extract_pages('ict mentorship.pdf', 227, 238, 'month3_video6_raw.txt')
