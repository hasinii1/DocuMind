from types import SimpleNamespace

from app.api.v1 import documents


def test_document_download_is_inline(monkeypatch, tmp_path):
    pdf_path = tmp_path / "summary-notes.pdf"
    pdf_path.write_bytes(b"%PDF-1.7 test")
    document = SimpleNamespace(
        storage_path=str(pdf_path),
        mime_type="application/pdf",
        original_filename=pdf_path.name,
    )
    monkeypatch.setattr(
        documents,
        "verify_document_access",
        lambda db, user, document_id: document,
    )

    response = documents.download_document_file(
        document_id="document-id",
        user=None,
        db=None,
    )

    assert response.headers["content-disposition"] == 'inline; filename="summary-notes.pdf"'
