package com.smartinbox.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.smartinbox.dto.ai.*;
import com.smartinbox.entity.*;
import com.smartinbox.model.Category;
import com.smartinbox.model.PdfType;
import com.smartinbox.model.ReviewerStatus;
import com.smartinbox.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.FileUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.File;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class DocumentProcessingService {

    private final AiServiceClient aiServiceClient;
    private final AuditService auditService;
    private final MessageRepository messageRepository;
    private final AttachmentRepository attachmentRepository;
    private final PdfSummaryRepository pdfSummaryRepository;
    private final PdfTableRepository pdfTableRepository;
    private final PdfImageRepository pdfImageRepository;
    private final PdfTranslationRepository pdfTranslationRepository;
    private final ClassificationRepository classificationRepository;
    private final ExtractedFieldRepository extractedFieldRepository;
    private final ObjectMapper objectMapper;

    @Transactional
    public void processMessage(Long messageId) throws Exception {
        Message message = messageRepository.findById(messageId)
                .orElseThrow(() -> new IllegalArgumentException("Message not found: " + messageId));

        log.info("Starting document processing pipeline for message ID: {} subject='{}'", messageId, message.getSubject());

        List<Attachment> attachments = attachmentRepository.findByMessageId(messageId);
        List<ClassifyAiRequest.PdfExtractionItem> pdfExtractions = new ArrayList<>();

        // 1. Process all PDF attachments (Max 1 call per PDF)
        for (Attachment att : attachments) {
            if (!att.isPdf() || att.isLoggedOnly()) {
                log.info("Skipping non-PDF or logged-only attachment: {}", att.getFilename());
                continue;
            }

            File pdfFile = new File(att.getStoragePath());
            if (!pdfFile.exists()) {
                File fallback = new File("..", att.getStoragePath());
                if (fallback.exists()) {
                    pdfFile = fallback;
                } else {
                    log.warn("Attachment file not found at path: {}", att.getStoragePath());
                    continue;
                }
            }

            byte[] fileBytes = FileUtils.readFileToByteArray(pdfFile);
            String pdfBase64 = Base64.getEncoder().encodeToString(fileBytes);

            ProcessDocumentAiRequest docRequest = ProcessDocumentAiRequest.builder()
                    .filename(att.getFilename())
                    .pdfBase64(pdfBase64)
                    .emailContext(ProcessDocumentAiRequest.EmailContext.builder()
                            .subject(message.getSubject())
                            .bodySnippet(message.getBodyText() != null ? message.getBodyText().substring(0, Math.min(500, message.getBodyText().length())) : "")
                            .build())
                    .build();

            log.info("Processing PDF attachment ID: {} filename: {}", att.getId(), att.getFilename());
            ProcessDocumentAiResponse docResponse = aiServiceClient.processDocument(docRequest);

            // Persist PDF type
            if (docResponse.getPdfType() != null) {
                try {
                    att.setPdfType(PdfType.valueOf(docResponse.getPdfType().toUpperCase()));
                } catch (Exception e) {
                    att.setPdfType(PdfType.DIGITAL);
                }
                attachmentRepository.save(att);
            }

            // Persist Summary (Upsert)
            if (docResponse.getSummary() != null) {
                PdfSummary summary = pdfSummaryRepository.findByAttachmentId(att.getId()).orElse(null);
                if (summary == null) {
                    summary = PdfSummary.builder().attachment(att).build();
                }
                summary.setSummaryText(docResponse.getSummary());
                summary.setRelevanceOpinion(docResponse.getRelevanceOpinion());
                summary.setRelevanceReason(docResponse.getRelevanceReason());
                pdfSummaryRepository.save(summary);
            }

            // Persist structured Tables (Never flattened)
            if (docResponse.getTables() != null) {
                pdfTableRepository.deleteByAttachmentId(att.getId());
                for (ProcessDocumentAiResponse.TableData tableData : docResponse.getTables()) {
                    String tableJson = objectMapper.writeValueAsString(tableData.getRows());
                    PdfTable table = PdfTable.builder()
                            .attachment(att)
                            .pageNumber(tableData.getPage() != null ? tableData.getPage() : 1)
                            .tableJson(tableJson)
                            .build();
                    pdfTableRepository.save(table);
                }
            }

            // Persist Images with review flag
            if (docResponse.getImages() != null) {
                pdfImageRepository.deleteByAttachmentId(att.getId());
                for (ProcessDocumentAiResponse.ImageData img : docResponse.getImages()) {
                    PdfImage pdfImage = PdfImage.builder()
                            .attachment(att)
                            .pageNumber(img.getPage() != null ? img.getPage() : 1)
                            .description(img.getDescription())
                            .reviewFlag(img.isReviewFlag())
                            .build();
                    pdfImageRepository.save(pdfImage);
                }
            }

            // Persist Translation (if NON_ENGLISH, Upsert)
            if (docResponse.getTranslation() != null && docResponse.getTranslation().getTranslatedText() != null) {
                PdfTranslation trans = pdfTranslationRepository.findByAttachmentId(att.getId()).orElse(null);
                if (trans == null) {
                    trans = PdfTranslation.builder().attachment(att).build();
                }
                trans.setSourceLanguage(docResponse.getTranslation().getSourceLanguage());
                trans.setOriginalTextRef(docResponse.getTranslation().getOriginalTextRef());
                trans.setTranslatedText(docResponse.getTranslation().getTranslatedText());
                pdfTranslationRepository.save(trans);
            }

            // Record extraction for next step
            pdfExtractions.add(ClassifyAiRequest.PdfExtractionItem.builder()
                    .attachmentId(att.getId())
                    .extractedText(docResponse.getExtractedText() != null ? docResponse.getExtractedText() : "")
                    .tables(new ArrayList<>(docResponse.getTables() != null ? docResponse.getTables() : List.of()))
                    .build());

            auditService.logAiDecision("ATTACHMENT", att.getId(), "PROCESS_DOCUMENT", docResponse);
        }

        // 2. Classify and Extract Facts for entire Message (Max 1 call per message)
        ClassifyAiRequest classifyRequest = ClassifyAiRequest.builder()
                .sender(message.getSender())
                .subject(message.getSubject())
                .emailBody(message.getBodyText() != null ? message.getBodyText() : "")
                .pdfExtractions(pdfExtractions)
                .build();

        log.info("Classifying and extracting facts for message ID: {}", messageId);
        ClassifyAiResponse classifyResponse = aiServiceClient.classifyAndExtract(classifyRequest);

        // Clear previous classifications and extracted fields before re-persisting
        classificationRepository.deleteByMessageId(message.getId());
        extractedFieldRepository.deleteByMessageId(message.getId());

        // Persist Classifications
        if (classifyResponse.getClassifications() != null) {
            for (ClassifyAiResponse.ClassificationItem item : classifyResponse.getClassifications()) {
                try {
                    Category cat = Category.valueOf(item.getCategory().toUpperCase());
                    Classification classification = Classification.builder()
                            .message(message)
                            .category(cat)
                            .confidence(item.getConfidence())
                            .reason(item.getReason())
                            .reviewerStatus(ReviewerStatus.PENDING)
                            .build();
                    classificationRepository.save(classification);
                } catch (Exception e) {
                    log.warn("Unknown category received from AI: {}", item.getCategory());
                }
            }
        }

        // Persist Extracted Fields
        saveSafetyReportFields(message, classifyResponse.getSafetyReportFields());
        saveQualityComplaintFields(message, classifyResponse.getQualityComplaintFields());
        saveInfoRequestFields(message, classifyResponse.getInfoRequestFields());

        auditService.logAiDecision("MESSAGE", message.getId(), "CLASSIFY_AND_EXTRACT", classifyResponse);
        log.info("Document processing pipeline successfully completed for message ID: {}", messageId);
    }

    private void saveSafetyReportFields(Message message, ClassifyAiResponse.SafetyReportFields sr) {
        if (sr == null) return;

        if (sr.getPatient() != null) {
            saveField(message, "PATIENT", "age", sr.getPatient().getAge());
            saveField(message, "PATIENT", "sex", sr.getPatient().getSex());
            saveField(message, "PATIENT", "weightHeight", sr.getPatient().getWeightHeight());
            saveField(message, "PATIENT", "relevantHistory", sr.getPatient().getRelevantHistory());
        }
        if (sr.getReporter() != null) {
            saveField(message, "REPORTER", "name", sr.getReporter().getName());
            saveField(message, "REPORTER", "role", sr.getReporter().getRole());
            saveField(message, "REPORTER", "country", sr.getReporter().getCountry());
        }
        if (sr.getProduct() != null) {
            saveField(message, "PRODUCT", "name", sr.getProduct().getName());
            saveField(message, "PRODUCT", "dose", sr.getProduct().getDose());
            saveField(message, "PRODUCT", "route", sr.getProduct().getRoute());
            saveField(message, "PRODUCT", "startDate", sr.getProduct().getStartDate());
            saveField(message, "PRODUCT", "stopDate", sr.getProduct().getStopDate());
        }
        if (sr.getReaction() != null) {
            saveField(message, "REACTION", "description", sr.getReaction().getDescription());
            saveField(message, "REACTION", "onset", sr.getReaction().getOnset());
            saveField(message, "REACTION", "outcome", sr.getReaction().getOutcome());
        }
        if (sr.getSeverity() != null) {
            saveField(message, "SEVERITY", "level", sr.getSeverity().getLevel());
        }
        if (sr.getNarrative() != null) {
            saveField(message, "NARRATIVE", "narrative", sr.getNarrative());
        }
    }

    private void saveQualityComplaintFields(Message message, ClassifyAiResponse.QualityComplaintFields qc) {
        if (qc == null) return;
        saveField(message, "QC", "productBatchLot", qc.getProductBatchLot());
        saveField(message, "QC", "defectDescription", qc.getDefectDescription());
        saveField(message, "QC", "photoMentioned", qc.getPhotoMentioned());
    }

    private void saveInfoRequestFields(Message message, ClassifyAiResponse.InfoRequestFields ir) {
        if (ir == null || ir.getQuestions() == null) return;
        int idx = 1;
        for (ClassifyAiResponse.InfoRequestQuestion q : ir.getQuestions()) {
            ExtractedField field = ExtractedField.builder()
                    .message(message)
                    .fieldGroup("INFO_REQUEST")
                    .fieldName("question_" + idx)
                    .fieldValue(q.getQuestion() + " (Topic: " + (q.getProductTopic() != null ? q.getProductTopic() : "General") + ")")
                    .confidence(q.getConfidence() != null ? q.getConfidence() : 0.9)
                    .sourceType(determineSourceType(q.getSourceRef()))
                    .sourceRef(q.getSourceRef() != null ? q.getSourceRef() : "email")
                    .reviewerEdited(false)
                    .build();
            extractedFieldRepository.save(field);
            idx++;
        }
    }

    private void saveField(Message message, String group, String name, ClassifyAiResponse.FieldValue fv) {
        if (fv == null) {
            fv = ClassifyAiResponse.FieldValue.builder().value("Not stated").build();
        }
        String val = (fv.getValue() == null || fv.getValue().isBlank()) ? "Not stated" : fv.getValue();
        Double conf = "Not stated".equalsIgnoreCase(val) ? null : fv.getConfidence();

        ExtractedField field = ExtractedField.builder()
                .message(message)
                .fieldGroup(group)
                .fieldName(name)
                .fieldValue(val)
                .confidence(conf)
                .sourceType(determineSourceType(fv.getSourceRef()))
                .sourceRef(fv.getSourceRef())
                .reviewerEdited(false)
                .build();
        extractedFieldRepository.save(field);
    }

    private String determineSourceType(String sourceRef) {
        if (sourceRef == null) return null;
        if (sourceRef.startsWith("attachment")) return "PDF_PAGE";
        return "EMAIL";
    }
}
