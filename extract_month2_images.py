"""
Render ICT Month 2 PDF pages 51-63 as PNG images for visual inspection.
Uses PyMuPDF (fitz) for high-quality rendering at 2x zoom.
"""
import fitz  # PyMuPDF
import os

PDF_PATH = r'd:\C.Slim\ict-intelligence\ict mentorship month 2.pdf'
OUT_DIR  = r'C:\Users\ESTHER\.gemini\antigravity\brain\a4ca42b4-0349-46e0-aa0e-51208f813b68\month2_pages'

os.makedirs(OUT_DIR, exist_ok=True)

doc = fitz.open(PDF_PATH)
total = len(doc)
print(f"Total pages in PDF: {total}")

# Pages 51-63 → indices 50-62
for page_num in range(50, min(63, total)):
    page = doc[page_num]
    # 2x zoom for clarity
    mat = fitz.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    out_path = os.path.join(OUT_DIR, f"page_{page_num + 1:02d}.png")
    pix.save(out_path)
    print(f"Saved: {out_path}")

doc.close()
print("\nDone. All pages rendered.")
