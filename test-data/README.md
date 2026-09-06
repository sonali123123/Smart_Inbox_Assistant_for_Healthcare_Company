# Test Data Set — README

This synthetic dataset was generated per `TEST_DATA_MANIFEST.md` for the Smart Inbox
Assistant prototype. All content is fictional (any real-format names/hospital details
appearing in the scanned images use conventions such as the reserved "555" phone
exchange to signal fictional use) and safe for use in a public repository or a live
demo — no real patient, provider, or product data appears anywhere in this dataset.

## What's here

| Path | Files | Description |
|------|-------|-------------|
| `emails/` | 13 `.eml` files | RFC-822 format emails (E01–E13). 9 of them contain PDF attachments embedded as MIME parts. |
| `pdfs/digital/` | 5 PDFs | Normal digital PDFs (P01–P05) — reference copies of the PDFs embedded inside the `.eml` files. |
| `pdfs/scanned/` | 2 PDFs | Scanned/handwritten PDFs (S01, S02) — reference copies of the PDFs embedded inside the `.eml` files. |
| `pdfs/nonenglish/` | 2 PDFs | Non-English PDFs: French (N01) and Japanese (N02) — reference copies of the PDFs embedded inside the `.eml` files. |
| `pdfs/article/` | 5 PDFs | Published-article-style PDFs with two-column layout (A01–A05). Used for Literature Screening. |

**Total: 27 files (13 emails + 14 PDFs).**

## Update: real photos/scans now included

The three files below originally shipped as labeled placeholders because authentic
photographic/handwritten content can't be faked with rendered fonts or vector
graphics. Real images have since been supplied and embedded:

| File | What was added |
|---|---|
| `pdfs/digital/pdf_digital_05_form_with_image.pdf` (P05) | A real photo of a pill bottle cap with a broken/peeled tamper-evident foil seal, embedded on page 2 of the form. |
| `pdfs/scanned/pdf_scanned_01_handwritten_form.pdf` (S01) | A real photo of a clearly handwritten adverse-event report (legible blue ballpoint), saved as a full-page scanned-style PDF. Intended to produce a **high** OCR confidence. |
| `pdfs/scanned/pdf_scanned_02_handwritten_low_legibility.pdf` (S02) | A real photo of a messier, photocopy-quality handwritten form with a smudged dose field and an ambiguous reporter-role abbreviation, saved as a full-page scanned-style PDF. Intended to produce a **lower** OCR confidence than S01. |

No placeholder boxes remain in the dataset. All 27 documents (13 emails + 14 PDFs)
are now complete and ready for processing.
