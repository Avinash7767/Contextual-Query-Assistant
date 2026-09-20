import fitz

from app.document.extractor import extract_pdf


def test_extract_pdf_preserves_page_text(tmp_path):
    path = tmp_path / "sample.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Payment Terms\nInvoices are due in 30 days.")
    document.save(path)
    document.close()

    pages = extract_pdf(path)

    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "Invoices are due in 30 days." in pages[0].text
