import pypdf
import os

def extract_images_from_pdf():
    pdf_path = "ict mentorship.pdf"
    output_dir = r"C:\Users\ESTHER\.gemini\antigravity\brain\747166f1-bd8e-4dfd-9717-20967047e27e"
    
    print(f"Opening {pdf_path}...")
    reader = pypdf.PdfReader(pdf_path)
    
    # Page indices are 0-based. Page 46 is index 45, Page 50 is index 49.
    for page_num in range(45, 51):
        print(f"Scanning Page {page_num + 1}...")
        page = reader.pages[page_num]
        
        for image_file_object in page.images:
            image_name = f"video8_page_{page_num + 1}_{image_file_object.name}"
            image_path = os.path.join(output_dir, image_name)
            
            with open(image_path, "wb") as fp:
                fp.write(image_file_object.data)
                
            print(f"Extracted: {image_name} ({len(image_file_object.data)} bytes)")

if __name__ == "__main__":
    extract_images_from_pdf()
