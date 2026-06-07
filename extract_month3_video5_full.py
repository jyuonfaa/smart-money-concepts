import pypdf
import os

def extract_video5_content():
    pdf_path = "ict mentorship.pdf"
    output_dir = r"C:\Users\ESTHER\.gemini\antigravity\brain\f64d08c6-7375-4d73-9b56-6d675b60f9e9"
    
    print(f"Opening {pdf_path}...")
    reader = pypdf.PdfReader(pdf_path)
    
    markdown_content = "# Month 3, Video 5: Inside Price Action - Institutional Market Structure\n\n"
    
    # Pages 216 to 226 (Indices 215 to 225)
    for page_num in range(215, 226):
        print(f"Scanning Page {page_num + 1}...")
        page = reader.pages[page_num]
        
        # Extract Text
        text = page.extract_text()
        markdown_content += f"## Page {page_num + 1}\n\n"
        markdown_content += text + "\n\n"
        
        # Extract Images
        for image_file_object in page.images:
            image_name = f"video5_page_{page_num + 1}_{image_file_object.name}"
            image_path = os.path.join(output_dir, image_name)
            
            with open(image_path, "wb") as fp:
                fp.write(image_file_object.data)
                
            print(f"Extracted Image: {image_name}")
            
            # Embed image in markdown
            markdown_content += f"\n![Page {page_num + 1} Image](file:///{image_path.replace(chr(92), '/')})\n\n"

    # Save the combined markdown artifact
    md_path = os.path.join(output_dir, "month3_video5_notes_with_images.md")
    with open(md_path, "w", encoding='utf-8') as f:
        f.write(markdown_content)
        
    print(f"\nExtraction complete. Saved to {md_path}")

if __name__ == "__main__":
    extract_video5_content()
