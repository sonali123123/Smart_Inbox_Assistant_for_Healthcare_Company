package com.smartinbox.service;

import com.smartinbox.config.AppProperties;
import com.smartinbox.dto.ai.*;
import com.smartinbox.entity.*;
import com.smartinbox.model.Category;
import com.smartinbox.model.PdfType;
import com.smartinbox.model.ReviewerStatus;
import com.smartinbox.model.SourceType;
import com.smartinbox.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.FileUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class LiteratureService {

    private final AppProperties appProperties;
    private final AiServiceClient aiServiceClient;
    private final AuditService auditService;
    private final MessageRepository messageRepository;
    private final AttachmentRepository attachmentRepository;
    private final LiteratureCaseRepository literatureCaseRepository;
    private final ClassificationRepository classificationRepository;
    private final ExtractedFieldRepository extractedFieldRepository;

    @Transactional
    public String processLiteratureBatch(List<MultipartFile> files) {
        String batchId = "lit-" + UUID.randomUUID().toString().substring(0, 8);
        log.info("Processing literature batch ID: {} with {} files", batchId, files.size());

        for (MultipartFile file : files) {
            try {
                processSingleArticle(batchId, file);
            } catch (Exception e) {
                log.error("Failed to process article {}: {}", file.getOriginalFilename(), e.getMessage(), e);
            }
        }
        return batchId;
    }

    private void processSingleArticle(String batchId, MultipartFile file) throws Exception {
        String filename = file.getOriginalFilename() != null ? file.getOriginalFilename() : "article.pdf";

        // Save file
        Path basePath = Paths.get(appProperties.getStorage().getPath());
        if (!Files.exists(basePath) && Files.exists(Paths.get("..").resolve(basePath))) {
            basePath = Paths.get("..").resolve(basePath);
        }
        Path storageDirPath = basePath.resolve("literature").resolve(batchId).toAbsolutePath().normalize();
        Files.createDirectories(storageDirPath);
        Path targetPath = storageDirPath.resolve(filename);
        File targetFile = targetPath.toFile();
        file.transferTo(targetFile);
        String storagePath = targetFile.getAbsolutePath();

        byte[] fileBytes = FileUtils.readFileToByteArray(targetFile);
        String pdfBase64 = Base64.getEncoder().encodeToString(fileBytes);

        // Step 1: Process document through /ai/process-document (REUSE)
        ProcessDocumentAiRequest docRequest = ProcessDocumentAiRequest.builder()
                .filename(filename)
                .pdfBase64(pdfBase64)
                .build();

        log.info("Step 1: Processing article PDF via AI: {}", filename);
        ProcessDocumentAiResponse docResponse = aiServiceClient.processDocument(docRequest);

        // Create a root literature message placeholder for the attachment
        Message rootMsg = Message.builder()
                .sourceType(SourceType.LITERATURE)
                .sender("Literature Batch: " + batchId)
                .subject(filename)
                .receivedDate(LocalDateTime.now())
                .bodyText("Published Literature Article: " + filename)
                .messageIdHeader("lit-source-" + UUID.randomUUID())
                .build();
        rootMsg = messageRepository.save(rootMsg);

        Attachment att = Attachment.builder()
                .message(rootMsg)
                .filename(filename)
                .contentType("application/pdf")
                .isPdf(true)
                .storagePath(storagePath)
                .pdfType(PdfType.ARTICLE)
                .loggedOnly(false)
                .build();
        att = attachmentRepository.save(att);

        // Step 2: Screen and split cases via /ai/literature-case-split
        LiteratureSplitAiRequest splitRequest = LiteratureSplitAiRequest.builder()
                .filename(filename)
                .articleText(docResponse.getExtractedText() != null ? docResponse.getExtractedText() : "")
                .tables(new ArrayList<>(docResponse.getTables() != null ? docResponse.getTables() : List.of()))
                .build();

        log.info("Step 2: Splitting literature cases for: {}", filename);
        LiteratureSplitAiResponse splitResponse = aiServiceClient.splitLiteratureCases(splitRequest);

        // Step 3: Persist each case as its own Message (source_type=LITERATURE) reusing core tables!
        if (splitResponse.getCases() != null) {
            for (LiteratureSplitAiResponse.LiteratureCaseItem caseItem : splitResponse.getCases()) {
                Message caseMessage = Message.builder()
                        .sourceType(SourceType.LITERATURE)
                        .sender("Literature Article: " + filename)
                        .subject(filename + " - Case #" + caseItem.getCaseIndex())
                        .receivedDate(LocalDateTime.now())
                        .bodyText(caseItem.getSummary())
                        .messageIdHeader("lit-case-" + UUID.randomUUID())
                        .build();
                caseMessage = messageRepository.save(caseMessage);

                // Thin link table
                LiteratureCase litCase = LiteratureCase.builder()
                        .batchId(batchId)
                        .message(caseMessage)
                        .sourceAttachment(att)
                        .caseIndex(caseItem.getCaseIndex() != null ? caseItem.getCaseIndex() : 1)
                        .isReportable(caseItem.isReportable())
                        .build();
                literatureCaseRepository.save(litCase);

                // Classification (SAFETY_REPORT if reportable, NOT_RELEVANT if not)
                Category category = caseItem.isReportable() ? Category.SAFETY_REPORT : Category.NOT_RELEVANT;
                Classification classification = Classification.builder()
                        .message(caseMessage)
                        .category(category)
                        .confidence(caseItem.isReportable() ? 0.95 : 0.90)
                        .reason(caseItem.getRelevanceReason())
                        .reviewerStatus(ReviewerStatus.PENDING)
                        .build();
                classificationRepository.save(classification);

                // Safety report fields if reportable
                if (caseItem.isReportable() && caseItem.getSafetyReportFields() != null) {
                    saveLiteratureSafetyFields(caseMessage, att.getId(), caseItem.getSafetyReportFields());
                }

                auditService.logAiDecision("LITERATURE_CASE", caseMessage.getId(), "SPLIT_CASE", caseItem);
            }
        }
    }

    private void saveLiteratureSafetyFields(Message message, Long attachmentId, ClassifyAiResponse.SafetyReportFields sr) {
        if (sr.getPatient() != null) {
            saveField(message, attachmentId, "PATIENT", "age", sr.getPatient().getAge());
            saveField(message, attachmentId, "PATIENT", "sex", sr.getPatient().getSex());
            saveField(message, attachmentId, "PATIENT", "weightHeight", sr.getPatient().getWeightHeight());
            saveField(message, attachmentId, "PATIENT", "relevantHistory", sr.getPatient().getRelevantHistory());
        }
        if (sr.getReporter() != null) {
            saveField(message, attachmentId, "REPORTER", "name", sr.getReporter().getName());
            saveField(message, attachmentId, "REPORTER", "role", sr.getReporter().getRole());
            saveField(message, attachmentId, "REPORTER", "country", sr.getReporter().getCountry());
        }
        if (sr.getProduct() != null) {
            saveField(message, attachmentId, "PRODUCT", "name", sr.getProduct().getName());
            saveField(message, attachmentId, "PRODUCT", "dose", sr.getProduct().getDose());
            saveField(message, attachmentId, "PRODUCT", "route", sr.getProduct().getRoute());
            saveField(message, attachmentId, "PRODUCT", "startDate", sr.getProduct().getStartDate());
            saveField(message, attachmentId, "PRODUCT", "stopDate", sr.getProduct().getStopDate());
        }
        if (sr.getReaction() != null) {
            saveField(message, attachmentId, "REACTION", "description", sr.getReaction().getDescription());
            saveField(message, attachmentId, "REACTION", "onset", sr.getReaction().getOnset());
            saveField(message, attachmentId, "REACTION", "outcome", sr.getReaction().getOutcome());
        }
        if (sr.getSeverity() != null) {
            saveField(message, attachmentId, "SEVERITY", "level", sr.getSeverity().getLevel());
        }
        if (sr.getNarrative() != null) {
            saveField(message, attachmentId, "NARRATIVE", "narrative", sr.getNarrative());
        }
    }

    private void saveField(Message message, Long attachmentId, String group, String name, ClassifyAiResponse.FieldValue fv) {
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
                .sourceType("PDF_PAGE")
                .sourceRef(fv.getSourceRef() != null ? fv.getSourceRef() : "attachment:" + attachmentId + ",page:1")
                .reviewerEdited(false)
                .build();
        extractedFieldRepository.save(field);
    }
}
