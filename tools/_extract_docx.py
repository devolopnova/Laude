#!/usr/bin/env python3
"""Script temporal, NO forma parte del pipeline permanente. Extrae el
texto literal (parrafos + tablas, en orden) de un .docx de la entrega
de Sillitas de coche, para copiarlo tal cual al HTML sin reescribir.
Uso: python tools/_extract_docx.py <ruta.docx> <salida.txt>
"""
import sys
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table

src = sys.argv[1]
out = sys.argv[2]

doc = Document(src)
lines = []
for el in doc.element.body:
    tag = el.tag.split("}")[-1]
    if tag == "p":
        para = Paragraph(el, doc)
        style = para.style.name if para.style else ""
        text = para.text
        if text.strip() or style.startswith("Heading"):
            lines.append(f"[{style}] {text}")
    elif tag == "tbl":
        tbl = Table(el, doc)
        cell_texts = []
        for row in tbl.rows:
            for cell in row.cells:
                cell_texts.append(cell.text)
        lines.append("[TABLE] " + " || ".join(cell_texts))

with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done", len(lines), "blocks")
