import fitz
import os

def create_markdown_with_images():
    pdf_path = r"d:\C.Slim\ict-intelligence\ict mentorship.pdf"
    output_dir = r"C:\Users\ESTHER\.gemini\antigravity\brain\f64d08c6-7375-4d73-9b56-6d675b60f9e9\month3_video3_assets"
    os.makedirs(output_dir, exist_ok=True)
    
    md_path = r"C:\Users\ESTHER\.gemini\antigravity\brain\f64d08c6-7375-4d73-9b56-6d675b60f9e9\month3_video3_full_notes.md"
    
    doc = fitz.open(pdf_path)
    
    md_content = "# Month 3 Video 3: Full Context Notes\n\n"
    
    # Pages 180 to 199 -> indices 179 to 198
    for page_num in range(179, 199):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        
        md_content += f"## --- Page {page_num + 1} ---\n\n"
        md_content += text + "\n\n"
        
        # Extract images
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            image_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
            image_path = os.path.join(output_dir, image_filename)
            
            # Use forward slashes for markdown path
            md_image_path = image_path.replace("\\", "/")
            
            with open(image_path, "wb") as f:
                f.write(image_bytes)
                
            md_content += f"\n![Page {page_num + 1} Image {img_index + 1}](/{md_image_path})\n\n"
            
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print(f"Markdown artifact created at: {md_path}")

if __name__ == "__main__":
    create_markdown_with_images()
