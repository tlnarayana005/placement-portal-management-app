from io import BytesIO

from flask import render_template
from xhtml2pdf import pisa


def render_pdf_from_template(template_name: str, context: dict):
    """
    Converts a Jinja2 HTML template into PDF bytes using xhtml2pdf.
    """
    html = render_template(template_name, **context)
    pdf_bytes = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_bytes)
    if pisa_status.err:
        raise RuntimeError(f"PDF generation failed: {pisa_status.err}")
    pdf_bytes.seek(0)
    return pdf_bytes.read()

