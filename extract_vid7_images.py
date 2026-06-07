import fitz
import os

pdf_path = r"d:\C.Slim\ict-intelligence\ict mentorship.pdf"
doc = fitz.open(pdf_path)

output_dir = r"d:\C.Slim\ict-intelligence\vid7_images"
os.makedirs(output_dir, exist_ok=True)

image_count = 0
for page_num in range(108, 131):
    try:
        page = doc.load_page(page_num)
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = os.path.join(output_dir, f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}")
            with open(image_filename, "wb") as f:
                f.write(image_bytes)
            image_count += 1
            print(f"Extracted: {image_filename}")
    except Exception as e:
        print(f"Error on page {page_num}: {e}")

print(f"Total images extracted: {image_count}")
