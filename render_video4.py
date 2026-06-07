import fitz
import os

PDF_PATH = r'd:\C.Slim\ict-intelligence\ict mentorship.pdf'
OUT_DIR  = r'C:\Users\ESTHER\.gemini\antigravity\brain\a4ca42b4-0349-46e0-aa0e-51208f813b68\scratch'

os.makedirs(OUT_DIR, exist_ok=True)

doc = fitz.open(PDF_PATH)
total = len(doc)
print(f"Total pages in PDF: {total}")

for page_num in range(74, min(81, total)):
    page = doc[page_num]
    mat = fitz.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    out_path = os.path.join(OUT_DIR, f"video4_page_{page_num + 1}.png")
    pix.save(out_path)
    print(f"Saved: {out_path}")

doc.close()
