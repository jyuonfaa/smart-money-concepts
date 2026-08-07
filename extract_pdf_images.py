import fitz
import sys

def pdf_to_images(pdf_path, start_page, end_page):
    try:
        doc = fitz.open(pdf_path)
        for i in range(start_page - 1, end_page):
            page = doc.load_page(i)
            # Render page to an image
            pix = page.get_pixmap(dpi=150)
            img_path = f"page_{i+1}.png"
            pix.save(img_path)
            print(f"Saved {img_path}")
    except Exception as e:
        print(f"Error extracting images: {e}")

if __name__ == '__main__':
    pdf_to_images('ict mentorship.pdf', 227, 238)
