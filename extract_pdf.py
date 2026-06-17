import pypdf
import sys

sys.stdout.reconfigure(encoding='utf-8')

pdf_path = r'\\spiderman\DEPARTMENTS\Project_Management_Office\Artificial_Intelligence\26_OBS Compare\1_Input\G-TRN_A08001_00_EN.pdf'
pdf = pypdf.PdfReader(pdf_path)

print(f'Total Pages: {len(pdf.pages)}\n')

for i, page in enumerate(pdf.pages):
    text = page.extract_text()
    if text and text.strip():
        print(f'--- Page {i+1} ---')
        print(text[:4000])
        print()
