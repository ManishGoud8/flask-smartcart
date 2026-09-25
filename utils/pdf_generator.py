# utils/pdf_generator.py
# -----------------------------------------------------------------------------
# DAY 14: PDF Generator Utility using xhtml2pdf
# Converts rendered HTML template string into in-memory PDF bytes buffer (BytesIO)
# -----------------------------------------------------------------------------
from xhtml2pdf import pisa
from io import BytesIO

def generate_pdf(template_html: str):
    """
    Takes rendered HTML string and returns a BytesIO buffer containing the PDF bytes.
    Returns None if an error occurs during conversion.
    """
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(template_html, dest=pdf_buffer)
    if pisa_status.err:
        return None
    pdf_buffer.seek(0)
    return pdf_buffer
