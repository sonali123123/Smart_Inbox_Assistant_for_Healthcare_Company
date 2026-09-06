package com.smartinbox.controller;

import com.smartinbox.dto.*;
import com.smartinbox.entity.*;
import com.smartinbox.model.ReviewerStatus;
import com.smartinbox.model.SourceType;
import com.smartinbox.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/messages")
@RequiredArgsConstructor
@Slf4j
public class MessageController {

    private final MessageRepository messageRepository;
    private final AttachmentRepository attachmentRepository;
    private final ClassificationRepository classificationRepository;
    private final ExtractedFieldRepository extractedFieldRepository;
    private final ReviewActionRepository reviewActionRepository;
    private final PdfSummaryRepository pdfSummaryRepository;
    private final PdfTableRepository pdfTableRepository;
    private final PdfImageRepository pdfImageRepository;
    private final PdfTranslationRepository pdfTranslationRepository;
    private final LiteratureCaseRepository literatureCaseRepository;
    private final com.smartinbox.service.MessageService messageService;

    @GetMapping
    @Transactional(readOnly = true)
    public ResponseEntity<Map<String, Object>> listMessages(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String sourceType
    ) {
        SourceType srcType = null;
        if (sourceType != null && !sourceType.isBlank()) {
            try {
                srcType = SourceType.valueOf(sourceType.toUpperCase());
            } catch (Exception ignored) {}
        }

        List<Message> allMessages = messageRepository.findAllWithDetails(srcType);
        List<MessageListItemDto> items = new ArrayList<>();

        for (Message m : allMessages) {
            // Exclude internal placeholder messages created only to hold literature source attachments
            if (m.getMessageIdHeader() != null && m.getMessageIdHeader().startsWith("lit-source-")) {
                continue;
            }

            List<Classification> classifications = classificationRepository.findByMessageId(m.getId());
            List<Attachment> attachments = new ArrayList<>(attachmentRepository.findByMessageId(m.getId()));
            if (attachments.isEmpty() && m.getSourceType() == SourceType.LITERATURE) {
                literatureCaseRepository.findByMessageId(m.getId())
                        .ifPresent(lc -> {
                            if (lc.getSourceAttachment() != null) {
                                attachments.add(lc.getSourceAttachment());
                            }
                        });
            }

            // Compute derived rollup status
            boolean hasPending = classifications.stream()
                    .anyMatch(c -> c.getReviewerStatus() == ReviewerStatus.PENDING);
            String derivedStatus = hasPending ? "PENDING_REVIEW" : "REVIEWED";

            // Status filter
            if (status != null && !status.isBlank() && !derivedStatus.equalsIgnoreCase(status)) {
                continue;
            }

            // Category filter
            if (category != null && !category.isBlank()) {
                boolean matchesCategory = classifications.stream()
                        .anyMatch(c -> c.getCategory().name().equalsIgnoreCase(category));
                if (!matchesCategory) {
                    continue;
                }
            }

            // Top summary: first PDF summary or email snippet
            String topSummary = "";
            for (Attachment att : attachments) {
                if (att.getSummary() != null && att.getSummary().getSummaryText() != null) {
                    topSummary = att.getSummary().getSummaryText();
                    break;
                }
            }
            if (topSummary.isBlank() && m.getBodyText() != null) {
                topSummary = m.getBodyText().substring(0, Math.min(250, m.getBodyText().length())) + "...";
            }

            List<ClassificationDto> classDtos = classifications.stream()
                    .map(c -> ClassificationDto.builder()
                            .id(c.getId())
                            .category(c.getCategory().name())
                            .confidence(c.getConfidence())
                            .reason(c.getReason())
                            .reviewerStatus(c.getReviewerStatus().name())
                            .build())
                    .collect(Collectors.toList());

            items.add(MessageListItemDto.builder()
                    .id(m.getId())
                    .sourceType(m.getSourceType().name())
                    .sender(m.getSender())
                    .subject(m.getSubject())
                    .receivedDate(m.getReceivedDate() != null ? m.getReceivedDate() : m.getCreatedAt())
                    .classifications(classDtos)
                    .topSummary(topSummary)
                    .status(derivedStatus)
                    .attachmentCount((int) attachments.stream().filter(Attachment::isPdf).count())
                    .build());
        }

        return ResponseEntity.ok(Map.of(
                "items", items,
                "total", items.size()
        ));
    }

    @GetMapping("/{id}")
    @Transactional(readOnly = true)
    public ResponseEntity<MessageDetailDto> getMessageDetail(@PathVariable Long id) {
        Message message = messageRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Message not found with ID: " + id));

        List<Classification> classifications = classificationRepository.findByMessageId(id);
        List<Attachment> attachments = new ArrayList<>(attachmentRepository.findByMessageId(id));
        if (attachments.isEmpty() && message.getSourceType() == SourceType.LITERATURE) {
            literatureCaseRepository.findByMessageId(id)
                    .ifPresent(lc -> {
                        if (lc.getSourceAttachment() != null) {
                            attachments.add(lc.getSourceAttachment());
                        }
                    });
        }
        List<ExtractedField> fields = extractedFieldRepository.findByMessageId(id);
        List<ReviewAction> reviewActions = reviewActionRepository.findByMessageIdOrderByTimestampDesc(id);

        boolean hasPending = classifications.stream()
                .anyMatch(c -> c.getReviewerStatus() == ReviewerStatus.PENDING);
        String derivedStatus = hasPending ? "PENDING_REVIEW" : "REVIEWED";

        List<ClassificationDto> classDtos = classifications.stream()
                .map(c -> ClassificationDto.builder()
                        .id(c.getId())
                        .category(c.getCategory().name())
                        .confidence(c.getConfidence())
                        .reason(c.getReason())
                        .reviewerStatus(c.getReviewerStatus().name())
                        .build())
                .collect(Collectors.toList());

        List<AttachmentDto> attDtos = attachments.stream().map(att -> {
            PdfSummary summary = pdfSummaryRepository.findByAttachmentId(att.getId()).orElse(null);
            PdfSummaryDto summaryDto = null;
            if (summary != null) {
                summaryDto = PdfSummaryDto.builder()
                        .id(summary.getId())
                        .summaryText(summary.getSummaryText())
                        .relevanceOpinion(summary.getRelevanceOpinion())
                        .relevanceReason(summary.getRelevanceReason())
                        .build();
            }

            List<PdfTable> tables = pdfTableRepository.findByAttachmentIdOrderByPageNumberAsc(att.getId());
            List<PdfTableDto> tableDtos = tables.stream().map(t -> PdfTableDto.builder()
                    .id(t.getId())
                    .pageNumber(t.getPageNumber())
                    .tableJson(t.getTableJson())
                    .build()).collect(Collectors.toList());

            List<PdfImage> images = pdfImageRepository.findByAttachmentIdOrderByPageNumberAsc(att.getId());
            List<PdfImageDto> imageDtos = images.stream().map(img -> PdfImageDto.builder()
                    .id(img.getId())
                    .pageNumber(img.getPageNumber())
                    .description(img.getDescription())
                    .reviewFlag(img.isReviewFlag())
                    .build()).collect(Collectors.toList());

            PdfTranslation translation = pdfTranslationRepository.findByAttachmentId(att.getId()).orElse(null);
            PdfTranslationDto transDto = null;
            if (translation != null) {
                transDto = PdfTranslationDto.builder()
                        .id(translation.getId())
                        .sourceLanguage(translation.getSourceLanguage())
                        .originalTextRef(translation.getOriginalTextRef())
                        .translatedText(translation.getTranslatedText())
                        .build();
            }

            return AttachmentDto.builder()
                    .id(att.getId())
                    .filename(att.getFilename())
                    .contentType(att.getContentType())
                    .isPdf(att.isPdf())
                    .pdfType(att.getPdfType() != null ? att.getPdfType().name() : null)
                    .loggedOnly(att.isLoggedOnly())
                    .summary(summaryDto)
                    .tables(tableDtos)
                    .images(imageDtos)
                    .translation(transDto)
                    .build();
        }).collect(Collectors.toList());

        List<ExtractedFieldDto> fieldDtos = fields.stream().map(f -> ExtractedFieldDto.builder()
                .id(f.getId())
                .attachmentId(f.getAttachment() != null ? f.getAttachment().getId() : null)
                .fieldGroup(f.getFieldGroup())
                .fieldName(f.getFieldName())
                .fieldValue(f.getFieldValue())
                .confidence(f.getConfidence())
                .sourceType(f.getSourceType())
                .sourceRef(f.getSourceRef())
                .reviewerEdited(f.isReviewerEdited())
                .build()).collect(Collectors.toList());

        List<ReviewActionDto> actionDtos = reviewActions.stream().map(a -> ReviewActionDto.builder()
                .id(a.getId())
                .reviewerName(a.getReviewerName())
                .action(a.getAction().name())
                .targetRef(a.getTargetRef())
                .previousValue(a.getPreviousValue())
                .newValue(a.getNewValue())
                .timestamp(a.getTimestamp())
                .build()).collect(Collectors.toList());

        MessageDetailDto detailDto = MessageDetailDto.builder()
                .id(message.getId())
                .sourceType(message.getSourceType().name())
                .sender(message.getSender())
                .subject(message.getSubject())
                .receivedDate(message.getReceivedDate() != null ? message.getReceivedDate() : message.getCreatedAt())
                .bodyText(message.getBodyText())
                .messageIdHeader(message.getMessageIdHeader())
                .createdAt(message.getCreatedAt())
                .status(derivedStatus)
                .classifications(classDtos)
                .attachments(attDtos)
                .extractedFields(fieldDtos)
                .reviewActions(actionDtos)
                .build();

        return ResponseEntity.ok(detailDto);
    }

    @PostMapping("/reset")
    public ResponseEntity<Map<String, Object>> resetData() {
        log.warn("API request received to reset all demo data");
        messageService.resetAllData();
        return ResponseEntity.ok(Map.of(
                "status", "SUCCESS",
                "message", "All demo messages, extracted facts, and audit logs have been cleanly reset."
        ));
    }

    @DeleteMapping
    public ResponseEntity<Map<String, Object>> deleteData() {
        return resetData();
    }
}
