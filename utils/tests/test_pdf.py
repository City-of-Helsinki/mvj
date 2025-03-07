from io import BytesIO
from unittest.mock import MagicMock

import pytest
from django.template import Context, Template
from pypdf import PdfReader  # via xhtml2pdf

from utils.pdf import PDFGenerationError, generate_pdf


@pytest.fixture
def mock_render_to_string(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("utils.pdf.render_to_string", mock)
    return mock


@pytest.fixture
def mock_create_pdf(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("utils.pdf.pisa.CreatePDF", mock)
    return mock


def _extract_text_from_pdf(pdf_content: BytesIO):
    pdf_reader = PdfReader(pdf_content)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


def test_generate_pdf_success(monkeypatch):
    template_content = "<html><body>Test {{ key }}</body></html>"
    template = Template(template_content)

    # Mock render_to_string to use the in-memory template
    def mock_render_to_string(template_name, context):
        return template.render(Context(context))

    monkeypatch.setattr("utils.pdf.render_to_string", mock_render_to_string)
    context = {"key": "kangaroo"}
    template_name = "test_pdf.html"

    pdf = generate_pdf(context, template_name)

    assert isinstance(pdf, BytesIO)
    pdf_text = _extract_text_from_pdf(pdf)
    assert "kangaroo" in pdf_text


def test_generate_pdf_failure(mock_render_to_string, mock_create_pdf):
    mock_render_to_string.return_value = "<html><body>Test</body></html>"
    mock_create_pdf.return_value = MagicMock(err=1)

    context = {"key": "value"}
    template_name = "template.html"

    with pytest.raises(PDFGenerationError):
        generate_pdf(context, template_name)

    mock_render_to_string.assert_called_once_with(template_name, context=context)
    mock_create_pdf.assert_called_once()
