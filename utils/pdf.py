from io import BytesIO
from typing import Any

from django.template.loader import render_to_string
from django.template.response import SimpleTemplateResponse, TemplateResponse
from xhtml2pdf import pisa


class PDFGenerationError(Exception):
    pass


def generate_pdf(context: dict[str, Any], template_name: str) -> BytesIO:
    html_source = render_to_string(template_name, context=context)
    output = BytesIO()
    pisa_status = pisa.CreatePDF(
        html_source,
        dest=output,
    )

    if pisa_status.err:
        raise PDFGenerationError("PDF generation failed.")

    output.seek(0)
    return output


class PdfResponse(TemplateResponse):
    def render(self) -> SimpleTemplateResponse:
        retval = super(PdfResponse, self).render()
        context = self.context_data or {}
        template_name = self.template_name
        if not isinstance(template_name, str):
            raise TypeError("PdfResponse requires a single template name.")
        pdf = generate_pdf(context, template_name)
        self.content = pdf.getvalue()
        return retval


class PdfMixin(object):
    content_type = "application/pdf"
    response_class = PdfResponse
