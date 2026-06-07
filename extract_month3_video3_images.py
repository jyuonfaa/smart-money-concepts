import pypdf
import os

def extract_images_from_pdf():
    pdf_path = "ict mentorship.pdf"
    # Create directory for images
    output_dir = r"C:\Users\ESTHER\.gemini\antigravity\brain\f64d08c6-7375-4d73-9b56-6d675b60f9e9\month3_video3_images"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Opening {pdf_path}...")
    reader = pypdf.PdfReader(pdf_path)
    
    # Page 180 is index 179. Pages 180 to 199 -> indices 179 to 198.
    extracted_images = []
    for page_num in range(179, 199):
        page = reader.pages[page_num]
        
        for image_file_object in page.images:
            image_name = f"page_{page_num + 1}_{image_file_object.name}"
            image_path = os.path.join(output_dir, image_name)
            
            with open(image_path, "wb") as fp:
                fp.write(image_file_object.data)
                
            extracted_images.append(image_path)
            print(f"Extracted: {image_name} ({len(image_file_object.data)} bytes)")
            
    # Generate an HTML file to view the images easily
    html_path = r"C:\Users\ESTHER\.gemini\antigravity\brain\f64d08c6-7375-4d73-9b56-6d675b60f9e9\view_month3_video3_images.html"
    html_content = "<html><body><h1>Month 3 Video 3 Images</h1>\n"
    for img in extracted_images:
        html_content += f"<h3>{os.path.basename(img)}</h3><img src='file:///{img.replace(chr(92), '/')}' style='max-width:100%'><br><hr>\n"
    html_content += "</body></html>"
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"\nHTML viewer created at: {html_path}")

if __name__ == "__main__":
    extract_images_from_pdf()
