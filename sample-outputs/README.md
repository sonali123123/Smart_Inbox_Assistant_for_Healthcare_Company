# Sample Outputs — Smart Inbox Assistant

This directory contains the sample outputs produced by the system across all synthetic test documents, satisfying **Deliverable #5** (*"Extracted JSON per test document, plus screenshots or a short screen recording of the review screen"*).

---

## 1. Directory Structure

```
sample-outputs/
├── README.md                                 # This manifest & guide
├── emails/                                   # Extracted JSON per test email (E01–E13)
│   ├── case_01_safety_full.json              # E01 + pdf_digital_01 (tables, clinical facts)
│   ├── case_02_safety_sparse.json            # E02 + pdf_digital_03 ("Not stated" fields)
│   ├── case_03_safety_plus_quality.json      # E03 (multi-label safety + quality defect)
│   ├── case_04_safety_with_pdf.json          # E04 + pdf_digital_02 (plain form pairing)
│   ├── case_05_quality_only_a.json           # E05 + pdf_digital_04 (QC form lot/batch)
│   ├── case_06_quality_only_b.json           # E06 + pdf_digital_05 (defect image flag)
│   ├── case_07_info_request_a.json           # E07 (single medical inquiry)
│   ├── case_08_info_request_b.json           # E08 (multi-question inquiry)
│   ├── case_09_not_relevant.json             # E09 (marketing/newsletter spam)
│   ├── case_10_safety_french.json            # E10 + pdf_nonenglish_01 (French translation)
│   ├── case_11_safety_scanned_high_ocr.json  # E11 + pdf_scanned_01 (handwritten OCR ~0.91)
│   ├── case_12_safety_scanned_low_ocr.json   # E12 + pdf_scanned_02 (low legibility OCR ~0.62)
│   └── case_13_safety_japanese.json          # E13 + pdf_nonenglish_02 (Japanese translation)
├── literature/                               # Bonus screening extractions (A01–A05)
│   ├── literature_42_article_01_single_case_pdf_Case_1.json
│   ├── literature_44_article_02_multi_case_pdf_Case_1.json
│   ├── literature_45_article_02_multi_case_pdf_Case_2.json
│   ├── literature_47_article_03_not_reportable_pdf_Case_.json
│   ├── literature_49_article_01_single_case_pdf_Case_1.json
│   ├── literature_51_article_02_multi_case_pdf_Case_1.json
│   ├── literature_52_article_02_multi_case_pdf_Case_2.json
│   └── ...
└── screenshots/                              # High-fidelity visual review evidence
    ├── 01_triage_queue_dashboard.png         # Main triage queue with filters & categories
    ├── 02_case_detail_review_screen.png      # Split review workbench with live PDF viewer & facts
    ├── 03_literature_screening_portal.png    # Standalone literature screening upload interface
    └── 04_batch_runner.png                   # Automated batch processing runner
```

---

## 2. Test Dataset Coverage Matrix

| Test File | Category | PDF Flavor | Key Feature Demonstrated | Output JSON |
|---|---|---|---|---|
| `email_01_safety_full.eml` | `SAFETY_REPORT` | `DIGITAL` | Structured lab values table (WBC, CRP, Eosinophils across 3 dates) | `emails/case_01_safety_full.json` |
| `email_02_safety_sparse.eml` | `SAFETY_REPORT` | `DIGITAL` | Zero-guessing mandate: missing fields set to `"Not stated"` with `confidence: null` | `emails/case_02_safety_sparse.json` |
| `email_03_safety_plus_quality.eml` | `SAFETY_REPORT` + `QUALITY_COMPLAINT` | None | Multi-label classification (damaged vial + reaction) | `emails/case_03_safety_plus_quality.json` |
| `email_04_safety_with_pdf.eml` | `SAFETY_REPORT` | `DIGITAL` | Dual-source citation: facts traced to `email` vs `attachment:10,page:1` | `emails/case_04_safety_with_pdf.json` |
| `email_05_quality_only_a.eml` | `QUALITY_COMPLAINT` | `DIGITAL` | QC intake form extraction (Lot/Batch number, defect description) | `emails/case_05_quality_only_a.json` |
| `email_06_quality_only_b.eml` | `QUALITY_COMPLAINT` | `DIGITAL` | Visual defect detection with factual description and review flag | `emails/case_06_quality_only_b.json` |
| `email_07_info_request_a.eml` | `INFO_REQUEST` | None | Clean informational inquiry classification | `emails/case_07_info_request_a.json` |
| `email_08_info_request_b.eml` | `INFO_REQUEST` | None | Multi-question medical inquiry extraction | `emails/case_08_info_request_b.json` |
| `email_09_not_relevant.eml` | `NOT_RELEVANT` | None | Marketing/newsletter spam filtering with low priority | `emails/case_09_not_relevant.json` |
| `email_10_safety_non_english.eml` | `SAFETY_REPORT` | `NON_ENGLISH` | French adverse event form translation and extraction | `emails/case_10_safety_french.json` |
| `email_11_safety_scanned.eml` | `SAFETY_REPORT` | `SCANNED` | High-confidence optical character recognition (`ocrConfidence: 0.91`) | `emails/case_11_safety_scanned_high_ocr.json` |
| `email_12_safety_scanned_2.eml` | `SAFETY_REPORT` | `SCANNED` | Degraded handwriting handling (`ocrConfidence: 0.62`) | `emails/case_12_safety_scanned_low_ocr.json` |
| `email_13_safety_japanese.eml` | `SAFETY_REPORT` | `NON_ENGLISH` | Japanese clinical summary translation and extraction | `emails/case_13_safety_japanese.json` |

---

## 3. JSON Output Schema Reference

Each document JSON output adheres to the enterprise safety review contract:

```json
{
  "id": 27,
  "sourceType": "EMAIL",
  "sender": "Dr. Alina Foster <a.foster@meridianclinic-example.ca>",
  "subject": "Adverse reaction report - patient hospitalized after Nortavex",
  "receivedDate": "2026-08-14T21:12:00",
  "status": "PENDING_REVIEW",
  "classifications": [
    {
      "category": "SAFETY_REPORT",
      "confidence": 1.0,
      "reason": "Patient R.K. experienced acute generalized urticaria...",
      "reviewerStatus": "PENDING"
    }
  ],
  "attachments": [
    {
      "filename": "pdf_digital_01_form_with_table.pdf",
      "pdfType": "DIGITAL",
      "summary": { "summaryText": "...", "relevanceOpinion": "RELEVANT" },
      "tables": [
        {
          "pageNumber": 2,
          "tableJson": "[[\"Lab Parameter\",\"13-Aug-2026\",\"14-Aug-2026\",\"15-Aug-2026\"],...]"
        }
      ],
      "images": [],
      "translation": null
    }
  ],
  "extractedFields": [
    {
      "fieldName": "name",
      "fieldGroup": "PRODUCT",
      "fieldValue": "Nortavex",
      "confidence": 1.0,
      "sourceType": "EMAIL",
      "sourceRef": "email",
      "reviewerEdited": false
    }
  ],
  "reviewActions": []
}
```

---

## 4. UI Review Screenshots

The `screenshots/` directory contains visual evidence captured from the running application:

### `01_triage_queue_dashboard.png`
* **Route:** `http://localhost:4200/messages`
* **Contents:**
  - Triage header with **Export CSV** and **Reset Demo Data** buttons.
  - Clinical KPI stat cards: *All Messages*, *Urgent SAEs*, *Quality Complaints*, and *Pending Review*.
  - Search filter by sender, subject, summary, and Source (Shared Mailbox vs Literature).
  - Triage table displaying category chips (`SAFETY_REPORT 95%`, `NOT_RELEVANT 90%`), urgency indicators (`WARNING`, `ROUTINE`), regulatory SLA countdown, and PDF attachment badges.

### `02_case_detail_review_screen.png`
* **Route:** `http://localhost:4200/messages/36` (Case #36: French clinic adverse event report)
* **Contents:**
  - **Left Pane (PDF Viewer):** Renders the native PDF document (*"Déclaration d'événement indésirable"*) with full document controls and zoom directly inside the browser viewport.
  - **Right Pane (AI Review Workbench):**
    - **Multi-Label Classification Card:** Shows `SAFETY_REPORT` (100% confidence) with AI clinical rationale and Accept / Override action buttons.
    - **Structured Facts Extraction Card:** Displays extracted clinical fields (Age: `59 years`, Sex: `Female`, Weight/Height: `68 kg / 165 cm`) with `100%` confidence chips linked to source citation `PDF Page 1`.
    - **Top Action Bar:** Reviewer identity (`Dr. Sarah Lin`) and **Approve & Next** button.
  - *Note on Headless vs. Real Browser:* Automated headless Chrome captures disable browser plugin rendering (resulting in an unrendered dark PDF box). In a standard browser session (as captured in `02_case_detail_review_screen.png`), the PDF displays cleanly alongside the extraction fields.

### `03_literature_screening_portal.png`
* **Route:** `http://localhost:4200/literature`
* **Contents:**
  - Drag-and-drop batch upload dropzone for published biomedical article PDFs.
  - One-click trigger for automated case identification, multi-patient splitting, and summary generation.

### `04_batch_runner.png`
* **Route:** `http://localhost:4200/batch`
* **Contents:**
  - Pipeline runner to execute batch document ingestion across all `.eml` and attached PDF files with latency tracking per file.

---

## 5. Live UI JSON Export

In addition to the pre-generated sample JSONs in this directory, evaluators can test live export directly in the web app:

1. **Queue View (`/messages`)**: Click the **Export JSON** button in the top right to download `PV_Triage_Queue_<date>.json`.
2. **Detail View (`/messages/:id`)**: Click the **Export JSON** button in the header to download `case_<id>_<subject_slug>.json`.
   - Before human edits: exports the pure AI extraction.
   - After human edits / overrides: exports the reviewed case with `reviewerEdited: true` and the full `reviewActions` audit trail.
