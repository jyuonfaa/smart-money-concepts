"""
Extract Month 2 content from ICT Mentorship Month 2 PDF.
Scans all pages, finds Month 2 / Video 1 section, prints verbatim.
"""
import pdfplumber

PDF_PATH = r'd:\C.Slim\ict-intelligence\ict mentorship month 2.pdf'

with pdfplumber.open(PDF_PATH) as pdf:
    total = len(pdf.pages)
    print(f"Total pages: {total}\n")

    # First pass — print page number + first 80 chars to build a map
    print("=== PAGE MAP ===")
    for i, page in enumerate(pdf.pages):
        text = (page.extract_text() or '').strip()
        first_line = text.split('\n')[0] if text else '[empty]'
        print(f"  Page {i+1:02d}: {first_line[:100]}")

    print("\n=== FULL TEXT (all pages) ===")
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ''
        print(f"\n{'='*60}")
        print(f"PAGE {i+1}")
        print('='*60)
        print(text)
