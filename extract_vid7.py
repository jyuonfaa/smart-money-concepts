import fitz

pdf_path = r"d:\C.Slim\ict-intelligence\ict mentorship.pdf"
doc = fitz.open(pdf_path)

with open("video7_extracted.md", "w", encoding="utf-8") as f:
    # Extracting a slightly wider range to account for offsets (1-indexed vs 0-indexed)
    # Page 110 to 129 as per user, we will extract 108 to 130 just to be safe
    for page_num in range(108, 131):
        try:
            page = doc.load_page(page_num)
            text = page.get_text()
            f.write(f"## Page {page_num + 1}\n\n")
            f.write(text)
            f.write("\n\n---\n\n")
        except Exception as e:
            f.write(f"Error on page {page_num}: {e}\n")

print("Done extracting pages to video7_extracted.md")
