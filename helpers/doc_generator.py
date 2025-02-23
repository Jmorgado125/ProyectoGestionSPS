# doc_generator.py
from docxtpl import DocxTemplate

def generate_pagare_docx(template_path, output_path, context):
    """
    Genera un documento .docx usando docxtpl, reemplazando los {{placeholders}}.
    """
    doc = DocxTemplate(template_path)
    doc.render(context)
    doc.save(output_path)
    return output_path
